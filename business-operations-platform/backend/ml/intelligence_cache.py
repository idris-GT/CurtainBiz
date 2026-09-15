from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock, Thread
from typing import Any, Callable

from fastapi.encoders import jsonable_encoder
from psycopg2.extras import Json

from app.database.connection import get_connection


# ---------------------------------------------------------------------------
# In-memory L1 cache
# ---------------------------------------------------------------------------

_CACHE: dict[tuple[str, int], dict[str, Any]] = {}

_LOCK = Lock()

_DB_INIT_LOCK = Lock()
_DB_READY = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_TABLE = "ml_intelligence_cache"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_table() -> None:
    """
    Create the persistent ML cache table if it does not already exist.

    This is intentionally done automatically so CurtainBiz does not need
    a separate migration just for the intelligence cache.
    """
    global _DB_READY

    if _DB_READY:
        return

    with _DB_INIT_LOCK:
        if _DB_READY:
            return

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {CACHE_TABLE} (
                    cache_name TEXT NOT NULL,
                    periods INTEGER NOT NULL,

                    status TEXT NOT NULL,
                    refreshing BOOLEAN NOT NULL DEFAULT FALSE,

                    started_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ,

                    data JSONB,
                    error TEXT,

                    PRIMARY KEY (cache_name, periods)
                )
                """
            )

            cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                idx_{CACHE_TABLE}_status
                ON {CACHE_TABLE} (status, refreshing)
                """
            )

            connection.commit()

            _DB_READY = True

            print(
                "[ML CACHE] Persistent cache table ready."
            )

        except Exception:
            if connection:
                connection.rollback()

            raise

        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()


def _copy_cache_item(
    item: dict[str, Any] | None,
) -> dict[str, Any] | None:
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


def _load_from_database(
    name: str,
    periods: int,
) -> dict[str, Any] | None:
    _ensure_table()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT
                status,
                refreshing,
                started_at,
                updated_at,
                data,
                error
            FROM {CACHE_TABLE}
            WHERE cache_name = %s
              AND periods = %s
            """,
            (name, int(periods)),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        status, refreshing, started_at, updated_at, data, error = row

        item = {
            "status": status,
            "refreshing": bool(refreshing),
            "started_at": (
                started_at.isoformat()
                if started_at
                else None
            ),
            "updated_at": (
                updated_at.isoformat()
                if updated_at
                else None
            ),
            "data": data,
            "error": error,
        }

        return item

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


def _save_to_database(
    name: str,
    periods: int,
    item: dict[str, Any],
) -> None:
    _ensure_table()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        data = item.get("data")

        if data is not None:
            data = jsonable_encoder(data)

        cursor.execute(
            f"""
            INSERT INTO {CACHE_TABLE} (
                cache_name,
                periods,
                status,
                refreshing,
                started_at,
                updated_at,
                data,
                error
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (cache_name, periods)
            DO UPDATE SET
                status = EXCLUDED.status,
                refreshing = EXCLUDED.refreshing,
                started_at = EXCLUDED.started_at,
                updated_at = EXCLUDED.updated_at,
                data = EXCLUDED.data,
                error = EXCLUDED.error
            """,
            (
                name,
                int(periods),
                item.get("status"),
                bool(item.get("refreshing", False)),
                item.get("started_at"),
                item.get("updated_at"),
                (
                    Json(
                        data,
                        dumps=lambda value: json.dumps(
                            value,
                            default=str,
                        ),
                    )
                    if data is not None
                    else None
                ),
                item.get("error"),
            ),
        )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ---------------------------------------------------------------------------
# Public cache read
# ---------------------------------------------------------------------------

def get_cached(
    name: str,
    periods: int,
) -> dict[str, Any] | None:
    """
    Get intelligence from the fastest available cache.

    L1:
        Process memory

    L2:
        PostgreSQL persistent cache

    A PostgreSQL hit is copied into the L1 cache so subsequent requests
    during the same process are extremely fast.
    """
    key = (name, int(periods))

    # ---------------------------------------------------------------
    # L1 memory cache
    # ---------------------------------------------------------------

    with _LOCK:
        item = _CACHE.get(key)

        if item is not None:
            return _copy_cache_item(item)

    # ---------------------------------------------------------------
    # L2 PostgreSQL cache
    # ---------------------------------------------------------------

    item = _load_from_database(
        name=name,
        periods=int(periods),
    )

    if item is None:
        return None

    # Store persistent result in L1 memory cache.
    with _LOCK:
        _CACHE[key] = item

    return _copy_cache_item(item)


# ---------------------------------------------------------------------------
# Background calculation
# ---------------------------------------------------------------------------

def _run_refresh(
    key: tuple[str, int],
    compute_fn: Callable[[], Any],
) -> None:
    name, periods = key

    with _LOCK:
        current = _CACHE.get(key)

    started_at = (
        current.get("started_at")
        if current
        else _now()
    )

    print(
        f"[ML CACHE] Background refresh started: "
        f"name={name}, periods={periods}"
    )

    try:
        result = compute_fn()

        completed_item = {
            "status": "success",
            "refreshing": False,
            "started_at": started_at,
            "updated_at": _now(),
            "data": result,
            "error": None,
        }

        # -----------------------------------------------------------
        # Save to RAM
        # -----------------------------------------------------------

        with _LOCK:
            _CACHE[key] = completed_item

        # -----------------------------------------------------------
        # Save permanently to PostgreSQL
        # -----------------------------------------------------------

        try:
            _save_to_database(
                name=name,
                periods=periods,
                item=completed_item,
            )

        except Exception as db_exc:
            print(
                f"[ML CACHE] PostgreSQL save FAILED: "
                f"name={name}, periods={periods}, "
                f"error={type(db_exc).__name__}: {db_exc}"
            )

            # Keep the successful RAM result even if DB persistence
            # temporarily fails.
            raise

        print(
            f"[ML CACHE] Background refresh completed: "
            f"name={name}, periods={periods}"
        )

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"

        with _LOCK:
            previous = _CACHE.get(key)

            error_item = {
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

            _CACHE[key] = error_item

        try:
            _save_to_database(
                name=name,
                periods=periods,
                item=error_item,
            )

        except Exception as db_exc:
            print(
                f"[ML CACHE] PostgreSQL error-state save FAILED: "
                f"name={name}, periods={periods}, "
                f"error={type(db_exc).__name__}: {db_exc}"
            )

        print(
            f"[ML CACHE] Background refresh FAILED: "
            f"name={name}, periods={periods}, "
            f"error={error_message}"
        )

        import traceback

        traceback.print_exc()


# ---------------------------------------------------------------------------
# Public refresh
# ---------------------------------------------------------------------------

def start_refresh(
    name: str,
    periods: int,
    compute_fn: Callable[[], Any],
) -> dict[str, Any]:
    """
    Start an intelligence calculation in the background.

    Important behavior:

    - If a refresh is already running, do NOT start another one.
    - Preserve the previous successful data while refreshing.
    - Persist processing state to PostgreSQL.
    - Persist successful results to PostgreSQL.
    """

    key = (name, int(periods))

    # Make sure the persistent table exists before starting.
    _ensure_table()

    # ---------------------------------------------------------------
    # Check existing persistent state first.
    #
    # This matters after a Render restart because RAM is empty but
    # PostgreSQL still knows whether another refresh is running.
    # ---------------------------------------------------------------

    with _LOCK:
        existing = _CACHE.get(key)

    if existing is None:
        existing = _load_from_database(
            name=name,
            periods=int(periods),
        )

        if existing is not None:
            with _LOCK:
                _CACHE[key] = existing

    # ---------------------------------------------------------------
    # Protect against duplicate refreshes.
    # ---------------------------------------------------------------

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

        processing_item = {
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

        _CACHE[key] = processing_item

    # ---------------------------------------------------------------
    # Persist processing state.
    # ---------------------------------------------------------------

    try:
        _save_to_database(
            name=name,
            periods=int(periods),
            item=processing_item,
        )

    except Exception as exc:
        # Do not prevent the ML calculation from running just because
        # the persistent cache has a temporary DB problem.
        print(
            f"[ML CACHE] Could not persist processing state: "
            f"name={name}, periods={periods}, "
            f"error={type(exc).__name__}: {exc}"
        )

    # ---------------------------------------------------------------
    # Start calculation.
    # ---------------------------------------------------------------

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
            "Intelligence refresh "
            "started in the background."
        ),
    }


# ---------------------------------------------------------------------------
# Clear cache
# ---------------------------------------------------------------------------

def clear_cache(
    name: str | None = None,
) -> None:
    """
    Clear both the RAM cache and PostgreSQL persistent cache.
    """

    _ensure_table()

    # ---------------------------------------------------------------
    # Clear RAM
    # ---------------------------------------------------------------

    with _LOCK:
        if name is None:
            _CACHE.clear()
        else:
            keys_to_remove = [
                key
                for key in _CACHE
                if key[0] == name
            ]

            for key in keys_to_remove:
                del _CACHE[key]

    # ---------------------------------------------------------------
    # Clear PostgreSQL
    # ---------------------------------------------------------------

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if name is None:
            cursor.execute(
                f"""
                DELETE FROM {CACHE_TABLE}
                """
            )
        else:
            cursor.execute(
                f"""
                DELETE FROM {CACHE_TABLE}
                WHERE cache_name = %s
                """,
                (name,),
            )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()