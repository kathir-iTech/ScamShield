import contextlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Dict, Iterator, Optional

from .context import get_request_context, get_request_id
from .log_config import LogConfig, load_config
from .tracing import get_trace_context

config: LogConfig = load_config()


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if config.format == "json":
            return self._format_json(record)
        return self._format_text(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id:
            entry["request_id"] = request_id
        trace = get_trace_context()
        trace_id = trace.get("trace_id", "")
        span_id = trace.get("span_id", "")
        if trace_id:
            entry["trace_id"] = trace_id
        if span_id:
            entry["span_id"] = span_id
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
            }
        extra = getattr(record, "extra_fields", None)
        if extra:
            entry.update(extra)
        return json.dumps(entry, default=str)

    def _format_text(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rid = get_request_id()
        trace = get_trace_context()
        tid = trace.get("trace_id", "")
        sid = trace.get("span_id", "")
        trace_str = ""
        if tid:
            trace_str = f" [{tid}:{sid}]" if sid else f" [{tid}]"
        prefix = f"[{rid}]" if rid else ""
        prefix = prefix + trace_str if prefix else trace_str.lstrip()
        return f"{ts} {prefix}[{record.levelname}] {record.name}: {record.getMessage()}"


class StructuredLogger(logging.Logger):
    def _log(
        self,
        level: int,
        msg: object,
        args: tuple,
        exc_info: Optional[tuple] = None,
        extra: Optional[dict] = None,
        **kwargs,
    ) -> None:
        if extra and "structured" in extra:
            kwargs["extra"] = {"extra_fields": extra["structured"]}
        elif extra:
            kwargs["extra"] = extra
        super()._log(level, msg, args, exc_info=exc_info, **kwargs)


logging.setLoggerClass(StructuredLogger)

logger = logging.getLogger("scamshield")
logger.setLevel(getattr(logging, config.level, logging.INFO))
logger.handlers.clear()

_formatter = StructuredFormatter()

if config.output in ("stdout", "both"):
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_formatter)
    stdout_handler.setLevel(getattr(logging, config.level, logging.INFO))
    logger.addHandler(stdout_handler)

if config.output in ("file", "both") and config.file_path:
    file_handler = RotatingFileHandler(
        config.file_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
    )
    file_handler.setFormatter(_formatter)
    file_handler.setLevel(getattr(logging, config.level, logging.INFO))
    logger.addHandler(file_handler)

logger.propagate = False


def reconfigure(cfg: LogConfig) -> None:
    global config
    config = cfg
    logger.setLevel(getattr(logging, config.level, logging.INFO))
    for handler in logger.handlers:
        handler.setLevel(getattr(logging, config.level, logging.INFO))


@contextlib.contextmanager
def log_duration(logger_instance: logging.Logger, operation: str, level: int = logging.INFO, **extra_fields) -> Iterator[None]:
    request_ctx = get_request_context()
    start = time.monotonic()
    logger_instance.log(
        level,
        "%s started",
        operation,
        extra={"structured": {"event": f"{operation}_start", "operation": operation, **extra_fields, **request_ctx}},
    )
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger_instance.log(
            level,
            "%s finished in %.3fs",
            operation,
            elapsed,
            extra={"structured": {"event": f"{operation}_finish", "operation": operation, "duration_s": round(elapsed, 3), **extra_fields, **request_ctx}},
        )


def log_exception_with_context(
    logger_instance: logging.Logger,
    exc: Exception,
    context: Optional[Dict] = None,
    level: int = logging.ERROR,
) -> None:
    request_ctx = get_request_context()
    extra_data = {**request_ctx}
    if context:
        extra_data.update(context)
    logger_instance.log(
        level,
        "%s: %s",
        type(exc).__name__,
        str(exc),
        exc_info=True,
        extra={"structured": {"exception_type": type(exc).__name__, "exception_message": str(exc), **extra_data}},
    )
