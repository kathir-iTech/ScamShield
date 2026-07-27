import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional

from .context import get_request_id
from .log_config import LogConfig, load_config

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
        prefix = f"[{rid}] " if rid else ""
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
