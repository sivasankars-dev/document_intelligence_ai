from fastapi import HTTPException, status

from shared.cache import get_cache_service


def enforce_rate_limit(key: str, limit: int, window_seconds: int):
    if limit <= 0:
        return

    cache = get_cache_service()
    count = cache.incr_with_ttl(key=key, ttl_seconds=window_seconds)
    if count is None:
        return

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
