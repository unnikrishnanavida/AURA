"""Structured agent logger.

Emits JSON-shaped, context-augmented log lines. Sensitive values (keys,
tokens, passwords) are redacted before emission so they are never written in
plaintext.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

__all__ = ["AgentLogger", "redact"]


_SENSITIVE_KEYS = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|authorization|auth|credential)", re.I
)


def redact(payload: dict) -> dict:
    """Return a deep copy of ``payload`` with sensitive values masked."""
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if _SENSITIVE_KEYS.search(key):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact(value)
        elif isinstance(value, list):
            result[key] = [
                redact(v) if isinstance(v, dict) else v for v in value
            ]
        else:
            result[key] = value
    return result


class AgentLogger:
    """Structured, level-aware logger bound to a Python ``logging`` logger."""

    def __init__(self, name: str = "aura.agent", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

    def _emit(self, level: int, event: str, *, context: dict | None = None, **fields) -> None:
        line = {
            "event": event,
            "context": context or {},
            **redact(fields),
        }
        self._logger.log(level, json.dumps(line, default=str))

    def info(self, event: str, *, context: dict | None = None, **fields) -> None:
        self._emit(logging.INFO, event, context=context, **fields)

    def warn(self, event: str, *, context: dict | None = None, **fields) -> None:
        self._emit(logging.WARNING, event, context=context, **fields)

    def error(self, event: str, *, context: dict | None = None, **fields) -> None:
        self._emit(logging.ERROR, event, context=context, **fields)

    def debug(self, event: str, *, context: dict | None = None, **fields) -> None:
        self._emit(logging.DEBUG, event, context=context, **fields)