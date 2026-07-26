"""Coordinator for the innovation subsystem."""

from __future__ import annotations

from typing import Any


class InnovationManager:
    """Manage the lifecycle of innovation components."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, item: Any) -> None:
        """Register a component."""
        self._items[name] = item

    def get(self, name: str) -> Any:
        """Return a registered component."""
        return self._items[name]

    def list(self) -> list[str]:
        """List registered component names."""
        return sorted(self._items)

    def remove(self, name: str) -> None:
        """Remove a registered component."""
        self._items.pop(name, None)
