from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.audit import record_suspicious_request
from core.logger import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if request.method in ("GET", "HEAD") and response.status_code < 300:
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "no-store"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def reset(self) -> None:
        self._requests.clear()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        now = time.monotonic()
        window_start = now - self.window_seconds
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]

        if len(self._requests[client_ip]) >= self.max_requests:
            from core.metrics import metrics
            metrics.record_rate_limit_event()
            logger.warning(
                "Rate limit exceeded for %s",
                client_ip,
                extra={"structured": {"client_ip": client_ip, "event": "rate_limit_exceeded"}},
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class RequestBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length_str = request.headers.get("content-length", "0")
        try:
            content_length = int(content_length_str)
        except (ValueError, TypeError):
            content_length = 0

        if content_length > self.max_body_size:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large. Maximum size is {self.max_body_size // (1024*1024)} MB."},
            )

        return await call_next(request)


_MAX_JSON_NESTING_DEPTH = 16
_MAX_JSON_FIELD_COUNT = 200
_MAX_JSON_ARRAY_LENGTH = 500


async def _validate_json_structure(body_bytes: bytes, client_ip: str) -> None:
    try:
        body_str = body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return

    body_str = body_str.strip()
    if not body_str:
        return

    try:
        parsed = json.loads(body_str)
    except json.JSONDecodeError:
        return

    def _check_depth(value: Any, depth: int = 0) -> int:
        if depth > _MAX_JSON_NESTING_DEPTH:
            return depth
        if isinstance(value, dict):
            if len(value) > _MAX_JSON_FIELD_COUNT:
                return depth
            for v in value.values():
                result = _check_depth(v, depth + 1)
                if result > _MAX_JSON_NESTING_DEPTH:
                    return result
        elif isinstance(value, list):
            if len(value) > _MAX_JSON_ARRAY_LENGTH:
                return depth
            for item in value:
                result = _check_depth(item, depth + 1)
                if result > _MAX_JSON_NESTING_DEPTH:
                    return result
        return depth

    max_depth = _check_depth(parsed)
    if max_depth > _MAX_JSON_NESTING_DEPTH:
        record_suspicious_request(
            detail=f"JSON nesting depth {max_depth} exceeds maximum {_MAX_JSON_NESTING_DEPTH}",
            client_ip=client_ip,
        )
        raise ValueError("JSON nesting too deep")


class JSONStructureValidator(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body = await request.body()
                if body:
                    try:
                        await _validate_json_structure(body, client_ip)
                    except ValueError as exc:
                        from fastapi.responses import JSONResponse

                        return JSONResponse(
                            status_code=422,
                            content={"detail": str(exc)},
                        )

        return await call_next(request)
