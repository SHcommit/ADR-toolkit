"""Structured stderr logging for ADR Toolkit commands.

stdout is a machine-readable JSON contract consumed by agents and CI --
never write anything else there. Diagnostic and crash logs go to stderr as
JSON Lines instead, tagged with a correlation ID so a failure reported in
the stdout JSON can be matched back to its log line.
"""
import json
import logging
import os
import sys
import time
import uuid
from typing import Optional

_LOG_LEVEL_ENV = "ADR_TOOLKIT_LOG_LEVEL"


class _JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname.lower(),
            "operation": getattr(record, "operation", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


def get_logger(operation: str, *, correlation_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Return a per-call logger bound to `operation`. The handler is
    rebuilt on every call (rather than cached on the module-level logger)
    so it always binds to the *current* sys.stderr -- this is what makes
    the logger correctly testable under pytest's capsys, and costs nothing
    in real usage since each CLI invocation is a fresh process that calls
    this exactly once."""
    logger = logging.getLogger("adr_toolkit")
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonLogFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    logger.setLevel(os.environ.get(_LOG_LEVEL_ENV, "WARNING").upper())
    return logging.LoggerAdapter(
        logger,
        {"operation": operation, "correlation_id": correlation_id or uuid.uuid4().hex[:12]},
    )
