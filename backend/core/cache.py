from __future__ import annotations

import functools
import json
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Union

_MISSING = object()

DEFAULT_TTL: float = 300.0
DEFAULT_MAXSIZE: int = 1024


class TTLCache:
    """Bounded LRU cache with per-entry TTL. Thread-safe."""

    def __init__(self, maxsize: int = DEFAULT_MAXSIZE, ttl: float = DEFAULT_TTL) -> None:
        self._maxsize = max(1, int(maxsize))
        self._ttl = float(ttl)
        self._data: "OrderedDict[str, tuple]" = OrderedDict()
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def ttl(self) -> float:
        return self._ttl

    def get(self, key: str, default: Any = None) -> Any:
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                self._misses += 1
                return default
            value, expires_at = item
            if expires_at <= now:
                del self._data[key]
                self._misses += 1
                return default
            self._data.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expires_at = time.monotonic() + (self._ttl if ttl is None else float(ttl))
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (value, expires_at)
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)
                self._evictions += 1

    def pop(self, key: str, default: Any = None) -> Any:
        with self._lock:
            item = self._data.pop(key, None)
        if item is None:
            return default
        value, expires_at = item
        if expires_at <= time.monotonic():
            return default
        return value

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def purge_expired(self) -> int:
        now = time.monotonic()
        with self._lock:
            expired = [key for key, (_, expires_at) in self._data.items() if expires_at <= now]
            for key in expired:
                del self._data[key]
        return len(expired)

    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "size": len(self._data),
                "maxsize": self._maxsize,
            }

    def __contains__(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return False
            if item[1] <= now:
                del self._data[key]
                return False
            self._data.move_to_end(key)
            return True

    def __len__(self) -> int:
        self.purge_expired()
        with self._lock:
            return len(self._data)


class RedisCache:
    """Same interface as TTLCache, backed by Redis. Fails open on every error."""

    def __init__(
        self,
        redis_url: str,
        ttl: float = DEFAULT_TTL,
        maxsize: int = DEFAULT_MAXSIZE,
        key_prefix: str = "scamshield:cache:",
    ) -> None:
        self._redis_url = redis_url
        self._ttl = float(ttl)
        self._maxsize = max(1, int(maxsize))
        self._prefix = key_prefix
        self._client: Any = None
        self._lock = threading.Lock()
        self._stats_lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._size: int = 0

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def ttl(self) -> float:
        return self._ttl

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def _conn(self) -> Any:
        with self._lock:
            if self._client is None:
                import redis as _redis

                self._client = _redis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
            return self._client

    def _count(self, field: str, delta: int = 1) -> None:
        with self._stats_lock:
            if field == "hits":
                self._hits += delta
            elif field == "misses":
                self._misses += delta
            elif field == "evictions":
                self._evictions += delta

    def get(self, key: str, default: Any = None) -> Any:
        try:
            raw = self._conn().get(self._key(key))
        except Exception:
            self._count("misses")
            return default
        if raw is None:
            self._count("misses")
            return default
        try:
            value = json.loads(raw)
        except (TypeError, ValueError):
            self._count("misses")
            return default
        self._count("hits")
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        try:
            raw = json.dumps(value, default=str)
            expires = int(ttl if ttl is not None else self._ttl)
            if expires < 1:
                expires = 1
            self._conn().set(self._key(key), raw, ex=expires)
            with self._stats_lock:
                self._size = min(self._size + 1, self._maxsize)
        except Exception:
            return

    def pop(self, key: str, default: Any = None) -> Any:
        value = self.get(key, _MISSING)
        if value is _MISSING:
            return default
        self.delete(key)
        return value

    def delete(self, key: str) -> None:
        try:
            self._conn().delete(self._key(key))
            with self._stats_lock:
                self._size = max(0, self._size - 1)
        except Exception:
            return

    def clear(self) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = self._conn().scan(cursor, match=f"{self._prefix}*", count=1000)
                if keys:
                    self._conn().delete(*keys)
                if cursor == 0:
                    break
            with self._stats_lock:
                self._size = 0
        except Exception:
            return

    def purge_expired(self) -> int:
        return 0

    def stats(self) -> Dict[str, int]:
        with self._stats_lock:
            size = self._size
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "size": size,
            "maxsize": self._maxsize,
        }

    def __contains__(self, key: str) -> bool:
        return self.get(key, _MISSING) is not _MISSING

    def __len__(self) -> int:
        with self._stats_lock:
            return self._size


Cache = Union[TTLCache, RedisCache]

_cache: Cache = TTLCache()


def get_cache() -> Cache:
    return _cache


def configure_cache(
    ttl: float = DEFAULT_TTL,
    maxsize: int = DEFAULT_MAXSIZE,
    redis_url: str = "",
) -> Cache:
    global _cache
    if redis_url:
        try:
            import redis  # noqa: F401
        except ImportError:
            _cache = TTLCache(maxsize=maxsize, ttl=ttl)
            return _cache
        _cache = RedisCache(redis_url, ttl=ttl, maxsize=maxsize)
        return _cache
    _cache = TTLCache(maxsize=maxsize, ttl=ttl)
    return _cache


def reset_cache() -> None:
    global _cache
    _cache = TTLCache()


def cached(key: str, ttl: Optional[float] = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()
            cache_key = f"{key}:{fn.__qualname__}:{args!r}:{sorted(kwargs.items())!r}"
            hit = cache.get(cache_key, _MISSING)
            if hit is not _MISSING:
                return hit
            value = fn(*args, **kwargs)
            cache.set(cache_key, value, ttl=ttl)
            return value

        return wrapper

    return decorator
