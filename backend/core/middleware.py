import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.context import (
    clear_request_context,
    get_user_id,
    set_request_context,
)
from core.logger import logger
from core.metrics import metrics


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()
        client_ip = request.client.host if request.client else ""
        correlation_id = request.headers.get("X-Correlation-ID", request_id)

        request.state.request_id = request_id
        request.state.start_time = start_time
        request.state.correlation_id = correlation_id

        set_request_context(
            request_id=request_id,
            start_time=start_time,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            correlation_id=correlation_id,
        )

        metrics.record_request_start()

        try:
            response: Response = await call_next(request)
        except Exception:
            metrics.record_request_end()
            clear_request_context()
            raise

        elapsed_ms = (time.monotonic() - start_time) * 1000

        level = "WARNING" if response.status_code >= 400 else "INFO"
        log_data = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "duration_ms": round(elapsed_ms, 1),
            "status_code": response.status_code,
            "method": request.method,
            "path": request.url.path,
        }
        uid = get_user_id()
        if uid:
            log_data["user_id"] = uid

        if logger.isEnabledFor(20):
            logger.log(
                20 if level == "INFO" else 30,
                "Request completed",
                extra={"structured": log_data},
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        metrics.record_request_end()
        clear_request_context()

        return response
