from __future__ import annotations

import time
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

    def reset(self) -> None:
        self._records.clear()

    def is_blocked(self, client_ip: str) -> bool:
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
        record = self._records.get(client_ip)
        if record and record.blocked_until > time.monotonic():
            return record.blocked_until - time.monotonic()
        return 0.0

    def record_request(self, client_ip: str, now: float) -> bool:
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
        record = self._records.get(client_ip)
        if record is None:
            return self.max_requests
        now = time.monotonic()
        window_start = now - self.window_seconds
        record.timestamps = [t for t in record.timestamps if t > window_start]
        return max(0, self.max_requests - len(record.timestamps))

    def reset_ip(self, client_ip: str) -> None:
        self._records.pop(client_ip, None)


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
