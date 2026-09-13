"""
Business Intelligence cache and background refresh engine.

Purpose:
    Keep expensive ML intelligence calculations out of the
    synchronous FastAPI request path.

Architecture:
    Database
        ↓
    ML pipeline
        ↓
    Intelligence calculation
        ↓
    In-memory cache
        ↓
    FastAPI
        ↓
    React
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable


# One worker is intentional.
#
# We do not want several expensive ML calculations consuming
# CPU/memory simultaneously.
_EXECUTOR = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="intelligence-refresh",
)

_CACHE: dict[tuple[str, int], dict[str, Any]] = {}

_LOCK = Lock()


def _utc_now() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(timezone.utc).isoformat()


def get_cached(
    name: str,
    periods: int,
) -> dict[str, Any] | None:
    """
    Return the cached intelligence state.

    Returns:
        None if no cache entry exists.
        Otherwise returns a copy of the cache state.
    """
    key = (name, periods)

    with _LOCK:
        entry = _CACHE.get(key)

        if entry is None:
            return None

        return dict(entry)


def start_refresh(
    name: str,
    periods: int,
    compute_fn: Callable[[], Any],
) -> dict[str, Any]:
    """
    Start a background intelligence calculation.

    If the same intelligence is already being calculated,
    do not start another calculation.

    Returns the current cache state immediately.
    """

    key = (name, periods)

    with _LOCK:
        existing = _CACHE.get(key)

        # Already calculating.
        if existing and existing.get("refreshing") is True:
            return dict(existing)

        # Preserve an existing successful result while refreshing.
        entry = {
            "status": "processing",
            "refreshing": True,
            "started_at": _utc_now(),
            "updated_at": (
                existing.get("updated_at")
                if existing
                else None
            ),
            "data": (
                existing.get("data")
                if existing
                else None
            ),
            "error": None,
        }

        _CACHE[key] = entry

    def _run() -> None:
        try:
            result = compute_fn()

            with _LOCK:
                _CACHE[key] = {
                    "status": "success",
                    "refreshing": False,
                    "started_at": entry["started_at"],
                    "updated_at": _utc_now(),
                    "data": result,
                    "error": None,
                }

        except Exception as exc:
            with _LOCK:
                previous = _CACHE.get(key)

                _CACHE[key] = {
                    "status": "error",
                    "refreshing": False,
                    "started_at": entry["started_at"],
                    "updated_at": (
                        previous.get("updated_at")
                        if previous
                        else None
                    ),
                    "data": (
                        previous.get("data")
                        if previous
                        else None
                    ),
                    "error": str(exc),
                }

    _EXECUTOR.submit(_run)

    with _LOCK:
        return dict(_CACHE[key])


def clear_cache(
    name: str | None = None,
) -> None:
    """
    Clear cached intelligence.

    If name is supplied:
        clear only entries belonging to that intelligence.

    If name is None:
        clear the complete cache.
    """

    with _LOCK:
        if name is None:
            _CACHE.clear()
            return

        keys_to_delete = [
            key
            for key in _CACHE
            if key[0] == name
        ]

        for key in keys_to_delete:
            del _CACHE[key]