import contextvars
import time
from typing import Dict, Optional

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")
start_time_var: contextvars.ContextVar[float] = contextvars.ContextVar("start_time", default=0.0)
method_var: contextvars.ContextVar[str] = contextvars.ContextVar("method", default="")
path_var: contextvars.ContextVar[str] = contextvars.ContextVar("path", default="")
client_ip_var: contextvars.ContextVar[str] = contextvars.ContextVar("client_ip", default="")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
pipeline_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("pipeline_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def get_correlation_id() -> str:
    return correlation_id_var.get()


def get_user_id() -> str:
    return user_id_var.get()


def get_pipeline_id() -> str:
    return pipeline_id_var.get()


def get_request_context() -> Dict[str, str]:
    ctx = {
        "request_id": request_id_var.get(),
        "correlation_id": correlation_id_var.get(),
        "method": method_var.get(),
        "path": path_var.get(),
        "client_ip": client_ip_var.get(),
    }
    uid = user_id_var.get()
    if uid:
        ctx["user_id"] = uid
    pid = pipeline_id_var.get()
    if pid:
        ctx["pipeline_id"] = pid
    return ctx


def set_request_context(
    request_id: str,
    start_time: float,
    method: str,
    path: str,
    client_ip: str,
    correlation_id: Optional[str] = None,
) -> None:
    request_id_var.set(request_id)
    correlation_id_var.set(correlation_id or request_id)
    start_time_var.set(start_time)
    method_var.set(method)
    path_var.set(path)
    client_ip_var.set(client_ip)


def set_user_id(user_id: str) -> None:
    user_id_var.set(user_id)


def set_pipeline_id(pipeline_id: str) -> None:
    pipeline_id_var.set(pipeline_id)


def clear_request_context() -> None:
    request_id_var.set("")
    correlation_id_var.set("")
    start_time_var.set(0.0)
    method_var.set("")
    path_var.set("")
    client_ip_var.set("")
    user_id_var.set("")
    pipeline_id_var.set("")
