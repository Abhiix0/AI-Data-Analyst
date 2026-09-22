"""Structured JSON logging and performance timing for AI Data Analyst."""
from __future__ import annotations
import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional


class JSONFormatter(logging.Formatter):
    """Custom logging formatter outputting standard JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "run_id"):
            log_obj["run_id"] = getattr(record, "run_id")
        if hasattr(record, "dataset_id"):
            log_obj["dataset_id"] = getattr(record, "dataset_id")
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = getattr(record, "duration_ms")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str = "ai_data_analyst", level: int = logging.INFO) -> logging.Logger:
    """Retrieve or configure a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger


@contextmanager
def timed_block(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Generator[Dict[str, Any], None, None]:
    """Context manager measuring execution duration and logging structured telemetry."""
    log = logger or get_logger("timer")
    start = time.perf_counter()
    ctx: Dict[str, Any] = {}
    try:
        yield ctx
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        extra_data = {**(extra or {}), **ctx, "duration_ms": duration_ms}
        log.info(f"{operation_name} completed in {duration_ms}ms", extra=extra_data)
