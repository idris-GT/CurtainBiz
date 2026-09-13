from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock, Thread
from typing import Any, Callable


_CACHE: dict[tuple[str, int], dict[str, Any]] = {}
_LOCK = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_cached(name: str, periods: int) -> dict[str, Any] | None:
    key = (name, int(periods))

    with _LOCK:
        item = _CACHE.get(key)

        if item is None:
            return None

        return {
            "status": item.get("status"),
            "refreshing": item.get("refreshing", False),
            "started_at": item.get("started_at"),
            "updated_at": item.get("updated_at"),
            "data": item.get("data"),
            "error": item.get("error"),
        }


def _run_refresh(
    key: tuple[str, int],
    compute_fn: Callable[[], Any],
) -> None:
    started_at = _now()

    print(
        f"[ML CACHE] Background refresh started: "
        f"name={key[0]}, periods={key[1]}"
    )

    try:
        result = compute_fn()

        with _LOCK:
            _CACHE[key] = {
                "status": "success",
                "refreshing": False,
                "started_at": started_at,
                "updated_at": _now(),
                "data": result,
                "error": None,
            }

        print(
            f"[ML CACHE] Background refresh completed: "
            f"name={key[0]}, periods={key[1]}"
        )

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"

        with _LOCK:
            previous = _CACHE.get(key)

            _CACHE[key] = {
                "status": "error",
                "refreshing": False,
                "started_at": started_at,
                "updated_at": _now(),
                "data": (
                    previous.get("data")
                    if previous
                    else None
                ),
                "error": error_message,
            }

        print(
            f"[ML CACHE] Background refresh FAILED: "
            f"name={key[0]}, periods={key[1]}, "
            f"error={error_message}"
        )

        import traceback

        traceback.print_exc()


def start_refresh(
    name: str,
    periods: int,
    compute_fn: Callable[[], Any],
) -> dict[str, Any]:
    key = (name, int(periods))

    with _LOCK:
        existing = _CACHE.get(key)

        if existing and existing.get("refreshing"):
            return {
                "status": "processing",
                "refreshing": True,
                "started_at": existing.get("started_at"),
                "updated_at": existing.get("updated_at"),
                "data": existing.get("data"),
                "message": (
                    "A refresh is already running."
                ),
            }

        previous_data = (
            existing.get("data")
            if existing
            else None
        )

        started_at = _now()

        _CACHE[key] = {
            "status": "processing",
            "refreshing": True,
            "started_at": started_at,
            "updated_at": (
                existing.get("updated_at")
                if existing
                else None
            ),
            "data": previous_data,
            "error": None,
        }

    thread = Thread(
        target=_run_refresh,
        args=(key, compute_fn),
        daemon=True,
        name=f"ml-refresh-{name}",
    )

    thread.start()

    return {
        "status": "processing",
        "refreshing": True,
        "started_at": started_at,
        "updated_at": (
            existing.get("updated_at")
            if existing
            else None
        ),
        "data": previous_data,
        "message": (
            "Admin Intelligence refresh "
            "started in the background."
        ),
    }


def clear_cache(name: str | None = None) -> None:
    with _LOCK:
        if name is None:
            _CACHE.clear()
            return

        keys_to_remove = [
            key
            for key in _CACHE
            if key[0] == name
        ]

        for key in keys_to_remove:
            del _CACHE[key]