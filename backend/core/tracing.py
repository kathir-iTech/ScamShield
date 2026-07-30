import contextvars
import random
from typing import Dict, Optional

from core.context import get_request_context

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")
parent_span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("parent_span_id", default="")
sampled_var: contextvars.ContextVar[bool] = contextvars.ContextVar("sampled", default=False)


def generate_trace_id() -> str:
    return format(random.getrandbits(128), "032x")


def generate_span_id() -> str:
    return format(random.getrandbits(64), "016x")


def get_trace_context() -> Dict[str, object]:
    return {
        "trace_id": trace_id_var.get(),
        "span_id": span_id_var.get(),
        "parent_span_id": parent_span_id_var.get(),
        "sampled": sampled_var.get(),
    }


def set_trace_context(
    trace_id: str = "",
    span_id: str = "",
    parent_span_id: str = "",
    sampled: bool = False,
) -> None:
    if trace_id:
        trace_id_var.set(trace_id)
    if span_id:
        span_id_var.set(span_id)
    if parent_span_id:
        parent_span_id_var.set(parent_span_id)
    sampled_var.set(sampled)


def clear_trace_context() -> None:
    trace_id_var.set("")
    span_id_var.set("")
    parent_span_id_var.set("")
    sampled_var.set(False)


def enrich_request_context() -> Dict[str, object]:
    ctx = get_request_context()
    trace = get_trace_context()
    ctx.update({k: v for k, v in trace.items() if v})
    return ctx
