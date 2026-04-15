import logging
from datetime import datetime, timedelta
from time import perf_counter
from typing import Callable, TypeVar

from fastapi import HTTPException, Response

logger = logging.getLogger(__name__)

CachedValue = TypeVar("CachedValue")

_read_cache: dict[str, dict[str, object]] = {}


def get_cached_resource(
    cache_key: str,
    ttl: timedelta,
    fetcher: Callable[[], CachedValue],
    label: str,
    error_detail: str,
    allow_stale: bool = True,
) -> tuple[CachedValue, str]:
    cached_entry = _read_cache.get(cache_key)
    now = datetime.now()

    if cached_entry and now - cached_entry["fetched_at"] <= ttl:
        logger.info("%s cache hit", label)
        return cached_entry["data"], "hit"

    started_at = perf_counter()

    try:
        data = fetcher()
    except HTTPException:
        raise
    except Exception as exc:
        elapsed = perf_counter() - started_at
        if cached_entry and allow_stale:
            logger.warning(
                "%s failed after %.2fs; serving stale cache: %s", label, elapsed, exc
            )
            return cached_entry["data"], "stale"

        logger.warning("%s failed after %.2fs without cache: %s", label, elapsed, exc)
        raise HTTPException(status_code=503, detail=error_detail) from exc

    _read_cache[cache_key] = {"data": data, "fetched_at": now}
    logger.info("%s cache miss resolved in %.2fs", label, perf_counter() - started_at)
    return data, "miss"


def apply_cache_headers(response: Response, cache_status: str, ttl: timedelta) -> None:
    response.headers["Cache-Control"] = f"public, max-age={int(ttl.total_seconds())}"
    response.headers["X-Cache"] = cache_status