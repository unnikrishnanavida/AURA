"""Core implementation for the storage subsystem."""

from __future__ import annotations

from typing import Any


class KeyValueStore:
    """A lightweight production-oriented implementation for storage."""

    def __init__(self) -> None:
        self._items: list[Any] = []

    def register(self, item: Any) -> None:
        """Register an item."""
        self._items.append(item)

    def list(self) -> list[Any]:
        """Return registered items."""
        return list(self._items)

    def clear(self) -> None:
        """Clear all registered items."""
        self._items.clear()
