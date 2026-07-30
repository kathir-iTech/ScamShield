from __future__ import annotations

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.logger import logger
from core.metrics import metrics


@dataclass
class IPRecord:
    timestamps: list[float] = field(default_factory=list)
    violations: int = 0
    blocked_until: float = 0.0


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._records: dict[str, IPRecord] = defaultdict(IPRecord)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def is_blocked(self, client_ip: str) -> bool:
        with self._lock:
            record = self._records.get(client_ip)
            if record is None:
                return False
            if record.blocked_until > time.monotonic():
                return True
            if record.blocked_until > 0:
                record.blocked_until = 0.0
                record.violations = 0
            return False

    def get_block_time(self, client_ip: str) -> float:
        with self._lock:
            record = self._records.get(client_ip)
            if record and record.blocked_until > time.monotonic():
                return record.blocked_until - time.monotonic()
            return 0.0

    def record_request(self, client_ip: str, now: float) -> bool:
        with self._lock:
            record = self._records[client_ip]
            window_start = now - self.window_seconds
            record.timestamps = [t for t in record.timestamps if t > window_start]

            if len(record.timestamps) >= self.max_requests:
                record.violations += 1
                if record.violations >= 3:
                    block_duration = min(60 * (2 ** (record.violations - 3)), 3600)
                    record.blocked_until = now + block_duration
                    logger.warning(
                        "IP %s blocked for %d seconds after %d violations",
                        client_ip, block_duration, record.violations,
                        extra={"structured": {"event": "ip_blocked", "client_ip": client_ip, "duration": block_duration}},
                    )
                return False

            record.timestamps.append(now)
            return True

    def remaining(self, client_ip: str) -> int:
        with self._lock:
            record = self._records.get(client_ip)
            if record is None:
                return self.max_requests
            now = time.monotonic()
            window_start = now - self.window_seconds
            record.timestamps = [t for t in record.timestamps if t > window_start]
            return max(0, self.max_requests - len(record.timestamps))

    def reset_ip(self, client_ip: str) -> None:
        with self._lock:
            self._records.pop(client_ip, None)


class RedisSlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis = None

    def _connect(self):
        from config.settings import REDIS_URL as _redis_url
        if self._redis is None:
            import redis as _redis
            self._redis = _redis.from_url(_redis_url, decode_responses=True)
            self._redis.ping()
        return self._redis

    def _key(self, client_ip: str, limiter_name: str = "default") -> str:
        return f"scamshield:ratelimit:{client_ip}:{limiter_name}"

    def is_blocked(self, client_ip: str, limiter_name: str = "default") -> bool:
        try:
            r = self._connect()
            key = self._key(client_ip, limiter_name)
            return bool(r.exists(key))
        except Exception as exc:
            logger.error("Redis is_blocked failed for %s/%s: %s", client_ip, limiter_name, exc,
                         extra={"structured": {"event": "redis_fail_closed", "client_ip": client_ip, "limiter": limiter_name}})
            return True

    def get_block_time(self, client_ip: str, limiter_name: str = "default") -> float:
        return 0.0

    def record_request(self, client_ip: str, now: float, limiter_name: str = "default") -> bool:
        try:
            r = self._connect()
            key = self._key(client_ip, limiter_name)
            min_score = now - self.window_seconds
            r.zremrangebyscore(key, 0, min_score)
            count = r.zcard(key)
            if count >= self.max_requests:
                return False
            r.zadd(key, {str(now): now})
            r.expire(key, self.window_seconds + 10)
            return True
        except Exception as exc:
            logger.error("Redis record_request failed for %s/%s: %s", client_ip, limiter_name, exc,
                         extra={"structured": {"event": "redis_fail_closed", "client_ip": client_ip, "limiter": limiter_name}})
            return False

    def remaining(self, client_ip: str, limiter_name: str = "default") -> int:
        try:
            r = self._connect()
            key = self._key(client_ip, limiter_name)
            now = time.monotonic()
            min_score = now - self.window_seconds
            r.zremrangebyscore(key, 0, min_score)
            count = r.zcard(key)
            return max(0, self.max_requests - count)
        except Exception as exc:
            logger.error("Redis remaining failed for %s/%s: %s", client_ip, limiter_name, exc,
                         extra={"structured": {"event": "redis_fail_closed", "client_ip": client_ip, "limiter": limiter_name}})
            return 0

    def reset(self) -> None:
        pass

    def reset_ip(self, client_ip: str, limiter_name: str = "default") -> None:
        try:
            r = self._connect()
            key = self._key(client_ip, limiter_name)
            r.delete(key)
        except Exception as exc:
            logger.error("Redis reset_ip failed for %s/%s: %s", client_ip, limiter_name, exc,
                         extra={"structured": {"event": "redis_fail_closed", "client_ip": client_ip, "limiter": limiter_name}})


def create_rate_limiter(name: str = "default", max_requests: int = 100, window_seconds: int = 60):
    from config.settings import REDIS_URL as _redis_url
    if _redis_url:
        try:
            import redis as _redis
            _client = _redis.from_url(_redis_url)
            _client.ping()
            _client.connection_pool.disconnect()
            return RedisSlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)
        except Exception:
            logger.warning(
                "Redis unavailable for rate limiter '%s' — falling back to in-memory",
                name,
                extra={"structured": {"event": "rate_limiter_fallback", "name": name}},
            )
    return SlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)


_limiter = SlidingWindowRateLimiter()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    return _limiter


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        global _limiter
        _limiter = SlidingWindowRateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        limiter = get_rate_limiter()

        if limiter.is_blocked(client_ip):
            block_time = limiter.get_block_time(client_ip)
            metrics.record_rate_limit_event()
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Your IP has been temporarily blocked."},
                headers={"Retry-After": str(int(block_time))},
            )

        now = time.monotonic()
        allowed = limiter.record_request(client_ip, now)

        if not allowed:
            metrics.record_rate_limit_event()
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(limiter.remaining(client_ip))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))
        return response
