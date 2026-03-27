import asyncio
import time
from collections import defaultdict, deque
from typing import Protocol, runtime_checkable

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, *, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - float(window_seconds)
        async with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


class RedisFixedWindowRateLimiter:
    """Fixed-window counter in Redis (shared across workers). Falls back to memory on failure."""

    def __init__(self, redis_url: str) -> None:
        from redis.asyncio import Redis
        from redis.exceptions import RedisError as RedisErr

        self._RedisError = RedisErr
        self._client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def allow(self, *, key: str, limit: int, window_seconds: int) -> bool:
        now = int(time.time())
        bucket = now // max(window_seconds, 1)
        rk = f"rl:{key}:{bucket}"
        try:
            pipe = self._client.pipeline()
            pipe.incr(rk)
            pipe.expire(rk, window_seconds)
            results = await pipe.execute()
            count = int(results[0])
            return count <= limit
        except self._RedisError as exc:
            log.warning("rate_limit_redis_error", error=str(exc))
            return await _memory_fallback.allow(key=key, limit=limit, window_seconds=window_seconds)


_memory_fallback = MemoryRateLimiter()


@runtime_checkable
class RateLimiterProtocol(Protocol):
    async def allow(self, *, key: str, limit: int, window_seconds: int) -> bool: ...


_limiter: RateLimiterProtocol | None = None


def get_rate_limiter() -> RateLimiterProtocol:
    global _limiter
    if _limiter is not None:
        return _limiter
    settings = get_settings()
    if settings.redis_url:
        try:
            _limiter = RedisFixedWindowRateLimiter(settings.redis_url)
            log.info("rate_limit_backend", backend="redis")
            return _limiter
        except Exception as exc:
            log.warning("rate_limit_backend", backend="memory", reason="redis_unavailable", error=str(exc))
    _limiter = MemoryRateLimiter()
    log.info("rate_limit_backend", backend="memory")
    return _limiter