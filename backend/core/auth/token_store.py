from __future__ import annotations

import abc
import time
from typing import Optional


class TokenStore(abc.ABC):
    @abc.abstractmethod
    def blacklist(self, jti: str, ttl: int = 0) -> None: ...

    @abc.abstractmethod
    def is_blacklisted(self, jti: str) -> bool: ...

    @abc.abstractmethod
    def mark_refresh_used(self, jti: str) -> bool: ...

    @abc.abstractmethod
    def is_refresh_reused(self, jti: str) -> bool: ...

    @abc.abstractmethod
    def reset(self) -> None: ...


class InMemoryTokenStore(TokenStore):
    def __init__(self, max_entries: int = 100000) -> None:
        self._blacklist: set[str] = set()
        self._used_refresh: set[str] = set()
        self._max_entries = max_entries

    def blacklist(self, jti: str, ttl: int = 0) -> None:
        self._blacklist.add(jti)
        if len(self._blacklist) > self._max_entries:
            self._blacklist.clear()

    def is_blacklisted(self, jti: str) -> bool:
        return jti in self._blacklist

    def mark_refresh_used(self, jti: str) -> bool:
        if jti in self._used_refresh:
            self._blacklist.add(jti)
            return False
        self._used_refresh.add(jti)
        if len(self._used_refresh) > self._max_entries:
            self._used_refresh.clear()
        return True

    def is_refresh_reused(self, jti: str) -> bool:
        return jti in self._used_refresh

    def reset(self) -> None:
        self._blacklist.clear()
        self._used_refresh.clear()


class RedisTokenStore(TokenStore):
    def __init__(self, redis_url: str, key_prefix: str = "scamshield:auth:") -> None:
        import redis as _redis
        self._redis = _redis.from_url(redis_url, decode_responses=True)
        self._prefix = key_prefix

    def _bk(self, jti: str) -> str:
        return f"{self._prefix}blacklist:{jti}"

    def _rk(self, jti: str) -> str:
        return f"{self._prefix}refresh:{jti}"

    def blacklist(self, jti: str, ttl: int = 0) -> None:
        self._redis.setex(self._bk(jti), ttl if ttl > 0 else 86400 * 30, "1")

    def is_blacklisted(self, jti: str) -> bool:
        return bool(self._redis.exists(self._bk(jti)))

    def mark_refresh_used(self, jti: str) -> bool:
        key = self._rk(jti)
        if self._redis.exists(key):
            self._redis.setex(self._bk(jti), 86400 * 30, "1")
            return False
        self._redis.setex(key, 86400 * 30, "1")
        return True

    def is_refresh_reused(self, jti: str) -> bool:
        return bool(self._redis.exists(self._rk(jti)))

    def reset(self) -> None:
        import redis as _redis
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor, match=f"{self._prefix}*", count=1000)
            if keys:
                self._redis.delete(*keys)
            if cursor == 0:
                break


_token_store: TokenStore = InMemoryTokenStore()


def get_token_store() -> TokenStore:
    return _token_store


def set_token_store(store: TokenStore) -> None:
    global _token_store
    _token_store = store


def create_token_store(redis_url: Optional[str] = None, max_entries: int = 100000) -> TokenStore:
    if redis_url:
        try:
            return RedisTokenStore(redis_url)
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "Redis URL configured but redis package not installed — falling back to in-memory store"
            )
    return InMemoryTokenStore(max_entries=max_entries)
