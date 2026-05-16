from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings, LogFormat

_EXTRA_FIELDS = ("entry_id", "query", "operation", "duration_ms", "count")


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        for key in _EXTRA_FIELDS:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


class _TextFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        return (
            f"{color}[{timestamp}] {record.levelname:<8}{self.RESET} "
            f"{record.name} -- {record.getMessage()}"
        )


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)

    if settings.log_format == LogFormat.JSON:
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(_TextFormatter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger
