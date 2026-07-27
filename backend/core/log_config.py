import os
from dataclasses import dataclass


@dataclass
class LogConfig:
    level: str = "INFO"
    format: str = "text"
    output: str = "stdout"
    file_path: str = ""
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5


def load_config() -> LogConfig:
    level = os.getenv("SCAMSHIELD_LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level not in valid_levels:
        level = "INFO"

    log_format = os.getenv("SCAMSHIELD_LOG_FORMAT", "text").lower()
    if log_format not in ("json", "text"):
        log_format = "text"

    output = os.getenv("SCAMSHIELD_LOG_OUTPUT", "stdout").lower()
    if output not in ("stdout", "file", "both"):
        output = "stdout"

    file_path = os.getenv("SCAMSHIELD_LOG_FILE", "")

    try:
        max_bytes = int(os.getenv("SCAMSHIELD_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
        if max_bytes < 1024:
            max_bytes = 10 * 1024 * 1024
    except (ValueError, TypeError):
        max_bytes = 10 * 1024 * 1024

    try:
        backup_count = int(os.getenv("SCAMSHIELD_LOG_BACKUP_COUNT", "5"))
        if backup_count < 0:
            backup_count = 5
    except (ValueError, TypeError):
        backup_count = 5

    return LogConfig(
        level=level,
        format=log_format,
        output=output,
        file_path=file_path,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )
