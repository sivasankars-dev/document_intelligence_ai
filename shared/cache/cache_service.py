import json
import time
from typing import Any

from shared.config.settings import settings


class CacheService:
    _redis_client = None
    _fallback_counters: dict[str, tuple[int, int]] = {}

    def __init__(self):
        if not settings.CACHE_ENABLED:
            return
        if CacheService._redis_client is None:
            CacheService._redis_client = self._init_redis_client()

    def _init_redis_client(self):
        try:
            import redis

            return redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
                retry_on_timeout=False,
            )
        except Exception:
            return None

    def get(self, key: str):
        if not settings.CACHE_ENABLED or self._redis_client is None:
            return None
        try:
            return self._redis_client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl_seconds: int):
        if not settings.CACHE_ENABLED or self._redis_client is None:
            return
        try:
            self._redis_client.setex(key, max(1, ttl_seconds), value)
        except Exception:
            return

    def delete(self, key: str):
        if not settings.CACHE_ENABLED or self._redis_client is None:
            return
        try:
            self._redis_client.delete(key)
        except Exception:
            return

    def get_json(self, key: str) -> Any:
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int):
        try:
            payload = json.dumps(value)
        except Exception:
            return
        self.set(key, payload, ttl_seconds)

    def incr_with_ttl(self, key: str, ttl_seconds: int):
        ttl_seconds = max(1, ttl_seconds)

        if settings.CACHE_ENABLED and self._redis_client is not None:
            try:
                count = self._redis_client.incr(key)
                if count == 1:
                    self._redis_client.expire(key, ttl_seconds)
                return int(count)
            except Exception:
                return None

        now = int(time.time())
        current = self._fallback_counters.get(key)
        if current is None or now >= current[1]:
            self._fallback_counters[key] = (1, now + ttl_seconds)
            return 1

        count, expires_at = current
        new_count = count + 1
        self._fallback_counters[key] = (new_count, expires_at)
        return new_count


_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
