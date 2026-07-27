from __future__ import annotations

import asyncio
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.logger import logger
from core.metrics import metrics


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_seconds: float = 30.0):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            from fastapi.responses import JSONResponse
            metrics.record_pipeline_failure()
            logger.error(
                "Request timed out after %s seconds on %s %s",
                self.timeout_seconds,
                request.method,
                request.url.path,
                extra={"structured": {"event": "request_timeout", "path": request.url.path}},
            )
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timed out. Please try again."},
            )


class CircuitBreakerState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    def allow_request(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True


_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, failure_threshold, recovery_timeout)
    return _breakers[name]


def retry(max_retries: int = 3, delay_seconds: float = 0.5, backoff: float = 2.0):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay_seconds
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        last_exception = exc
                        if attempt < max_retries:
                            logger.warning(
                                "Retry attempt %d/%d for %s after error: %s",
                                attempt + 1, max_retries,
                                getattr(func, "__name__", str(func)),
                                str(exc),
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                raise last_exception
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay_seconds
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as exc:
                        last_exception = exc
                        if attempt < max_retries:
                            logger.warning(
                                "Retry attempt %d/%d for %s after error: %s",
                                attempt + 1, max_retries,
                                getattr(func, "__name__", str(func)),
                                str(exc),
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                raise last_exception
            return sync_wrapper
    return decorator
