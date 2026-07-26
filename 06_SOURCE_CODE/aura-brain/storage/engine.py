"""Execution engine for the storage subsystem."""

from __future__ import annotations

from typing import Any


class StorageEngine:
    """Coordinate execution operations for storage."""

    def __init__(self) -> None:
        self._handlers: dict[str, Any] = {}

    def register(self, name: str, handler: Any) -> None:
        """Register a handler."""
        self._handlers[name] = handler

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered handler."""
        handler = self._handlers[name]
        return handler(*args, **kwargs)
