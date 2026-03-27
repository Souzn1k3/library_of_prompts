from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.config import get_settings
from app.core.logging import get_logger

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - redis is optional at runtime
    Redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        pass


log = get_logger(__name__)


class InMemoryCacheBackend:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float | None, str]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> str | None:
        async with self._lock:
            row = self._data.get(key)
            if row is None:
                return None
            expires_at, value = row
            if expires_at is not None and expires_at <= time.monotonic():
                self._data.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        expires_at = None if not ttl_seconds or ttl_seconds <= 0 else time.monotonic() + ttl_seconds
        async with self._lock:
            self._data[key] = (expires_at, value)

    async def incr(self, key: str) -> int:
        async with self._lock:
            current = self._data.get(key)
            if current is None:
                next_value = 1
            else:
                expires_at, raw = current
                if expires_at is not None and expires_at <= time.monotonic():
                    next_value = 1
                else:
                    try:
                        next_value = int(raw) + 1
                    except ValueError:
                        next_value = 1
            self._data[key] = (None, str(next_value))
            return next_value

    async def close(self) -> None:
        return None


class RedisCacheBackend:
    def __init__(self, redis_url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package is not available")
        self._client: Redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        if value is None:
            return None
        return str(value)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        if ttl_seconds and ttl_seconds > 0:
            await self._client.set(key, value, ex=ttl_seconds)
            return
        await self._client.set(key, value)

    async def incr(self, key: str) -> int:
        value = await self._client.incr(key)
        return int(value)

    async def close(self) -> None:
        await self._client.aclose()


class NamespaceCache:
    def __init__(
        self,
        *,
        redis_url: str | None,
        enabled: bool,
        key_prefix: str = "pv",
        default_ttl_seconds: int = 120,
    ) -> None:
        self._enabled = enabled
        self._key_prefix = key_prefix
        self._default_ttl = max(default_ttl_seconds, 1)
        self._fallback = InMemoryCacheBackend()
        self._redis_backend: RedisCacheBackend | None = None
        self._backend: InMemoryCacheBackend | RedisCacheBackend = self._fallback
        self._namespace_cache: dict[str, tuple[int, float]] = {}
        self._namespace_cache_ttl_seconds = 5.0
        self._namespace_lock = asyncio.Lock()
        self._uses_redis = False

        if redis_url:
            try:
                self._redis_backend = RedisCacheBackend(redis_url)
                self._backend = self._redis_backend
                self._uses_redis = True
                log.info("cache_backend_configured", backend="redis")
            except Exception:
                self._backend = self._fallback
                self._uses_redis = False
                log.warning("cache_backend_fallback", backend="memory", reason="redis_unavailable")
        else:
            log.info("cache_backend_configured", backend="memory")

    def _key(self, namespace: str, suffix: str) -> str:
        return f"{self._key_prefix}:{namespace}:{suffix}"

    def _namespace_version_key(self, namespace: str) -> str:
        return self._key("ns", f"{namespace}:version")

    async def _safe_get(self, key: str) -> str | None:
        try:
            return await self._backend.get(key)
        except RedisError:
            if self._uses_redis:
                self._uses_redis = False
                self._backend = self._fallback
                log.warning("cache_backend_runtime_fallback", backend="memory", reason="redis_error")
            return await self._fallback.get(key)

    async def _safe_set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        try:
            await self._backend.set(key, value, ttl_seconds)
        except RedisError:
            if self._uses_redis:
                self._uses_redis = False
                self._backend = self._fallback
                log.warning("cache_backend_runtime_fallback", backend="memory", reason="redis_error")
            await self._fallback.set(key, value, ttl_seconds)

    async def _safe_incr(self, key: str) -> int:
        try:
            return await self._backend.incr(key)
        except RedisError:
            if self._uses_redis:
                self._uses_redis = False
                self._backend = self._fallback
                log.warning("cache_backend_runtime_fallback", backend="memory", reason="redis_error")
            return await self._fallback.incr(key)

    async def _namespace_version(self, namespace: str) -> int:
        now = time.monotonic()
        cached = self._namespace_cache.get(namespace)
        if cached is not None and cached[1] > now:
            return cached[0]

        async with self._namespace_lock:
            cached = self._namespace_cache.get(namespace)
            if cached is not None and cached[1] > now:
                return cached[0]
            key = self._namespace_version_key(namespace)
            raw = await self._safe_get(key)
            if raw is None:
                version = 1
                await self._safe_set(key, str(version))
            else:
                try:
                    version = max(int(raw), 1)
                except ValueError:
                    version = 1
                    await self._safe_set(key, str(version))
            self._namespace_cache[namespace] = (version, now + self._namespace_cache_ttl_seconds)
            return version

    async def cache_key(self, *, namespace: str, suffix: str) -> str:
        version = await self._namespace_version(namespace)
        compact_suffix = suffix
        if len(compact_suffix) > 220:
            compact_suffix = hashlib.sha1(compact_suffix.encode("utf-8")).hexdigest()
        return self._key(namespace, f"v{version}:{compact_suffix}")

    async def get_json(self, *, namespace: str, suffix: str) -> Any | None:
        if not self._enabled:
            return None
        key = await self.cache_key(namespace=namespace, suffix=suffix)
        raw = await self._safe_get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(
        self,
        *,
        namespace: str,
        suffix: str,
        payload: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        if not self._enabled:
            return
        key = await self.cache_key(namespace=namespace, suffix=suffix)
        encoded = json.dumps(jsonable_encoder(payload), separators=(",", ":"), ensure_ascii=False)
        await self._safe_set(key, encoded, ttl_seconds or self._default_ttl)

    async def get_or_set_json(
        self,
        *,
        namespace: str,
        suffix: str,
        loader: Callable[[], Awaitable[Any]],
        ttl_seconds: int | None = None,
    ) -> Any:
        if not self._enabled:
            return await loader()

        existing = await self.get_json(namespace=namespace, suffix=suffix)
        if existing is not None:
            return existing

        payload = await loader()
        await self.set_json(
            namespace=namespace,
            suffix=suffix,
            payload=payload,
            ttl_seconds=ttl_seconds,
        )
        return payload

    async def bump(self, namespace: str) -> int:
        key = self._namespace_version_key(namespace)
        version = await self._safe_incr(key)
        self._namespace_cache[namespace] = (
            version,
            time.monotonic() + self._namespace_cache_ttl_seconds,
        )
        log.info("cache_namespace_bumped", namespace=namespace, version=version)
        return version

    async def bump_many(self, namespaces: list[str] | tuple[str, ...]) -> None:
        for namespace in namespaces:
            await self.bump(namespace)

    async def close(self) -> None:
        if self._redis_backend is not None:
            await self._redis_backend.close()
        await self._fallback.close()


_cache: NamespaceCache | None = None


def get_cache() -> NamespaceCache:
    global _cache
    if _cache is not None:
        return _cache

    settings = get_settings()
    _cache = NamespaceCache(
        redis_url=settings.redis_url,
        enabled=settings.cache_enabled,
        key_prefix="prompts-vault",
        default_ttl_seconds=settings.cache_default_ttl_seconds,
    )
    return _cache
