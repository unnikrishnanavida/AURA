"""Structured logging.

Logs are machine readable and carry correlation/execution ids so production
debugging can follow one unit of work end to end. Secrets are redacted by
default through the shared :class:`SecretRedactor`.
"""

from __future__ import annotations

import json
import sys
import threading
from typing import Any, TextIO

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import CorrelationId
from aura.observability.redaction import SecretRedactor

_LOGGERS: dict[str, StructuredLogger] = {}
_LOCK = threading.Lock()


class StructuredLogger:
    """JSON-structured, redacted logger."""

    def __init__(
        self,
        name: str,
        *,
        level: int | str = "INFO",
        stream: TextIO | None = None,
        redactor: SecretRedactor | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._name = name
        self._level = self._parse_level(level)
        self._stream = stream if stream is not None else sys.stderr
        self._redactor = redactor or SecretRedactor()
        self._clock = clock or SystemClock()

    @staticmethod
    def _parse_level(level: int | str) -> int:
        if isinstance(level, int):
            return level
        return {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "WARN": 30,
            "ERROR": 40,
        }.get(str(level).upper(), 20)

    def _log(self, level: str, message: str, *, correlation_id: CorrelationId | None = None, **fields: Any) -> None:
        record: dict[str, Any] = {
            "ts": self._clock.utcnow_iso(),
            "level": level,
            "logger": self._name,
            "message": message,
            "correlation_id": str(correlation_id) if correlation_id is not None else None,
        }
        for key, value in fields.items():
            if value is not None:
                record[key] = str(value)
        text = self._redactor.redact(json.dumps(record, sort_keys=True))
        self._stream.write(text + "\n")
        self._stream.flush()

    def debug(self, message: str, **fields: Any) -> None:
        if self._level <= 10:
            self._log("DEBUG", message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        if self._level <= 20:
            self._log("INFO", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        if self._level <= 30:
            self._log("WARNING", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        if self._level <= 40:
            self._log("ERROR", message, **fields)

    def bind_redactor(self, redactor: SecretRedactor) -> None:
        self._redactor = redactor


class RedactingLogger(StructuredLogger):
    """Alias retained for readability in engine imports."""


def get_logger(name: str, **kwargs: Any) -> StructuredLogger:
    """Return a cached structured logger for `name`."""
    with _LOCK:
        if name not in _LOGGERS:
            _LOGGERS[name] = StructuredLogger(name, **kwargs)
        return _LOGGERS[name]


__all__ = ["RedactingLogger", "StructuredLogger", "get_logger"]