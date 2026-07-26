"""Repository implementation for the events subsystem."""

from __future__ import annotations

from typing import Any


class EventsRepository:
    """In-memory repository for events objects."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def add(self, item: Any, name: str | None = None) -> None:
        """Add or update an item."""
        key = name or getattr(item, 'name', str(len(self._items)))
        self._items[key] = item

    def get(self, name: str) -> Any:
        """Retrieve an item by name."""
        return self._items[name]

    def list(self) -> list[Any]:
        """Return all stored items."""
        return list(self._items.values())

    def remove(self, name: str) -> None:
        """Remove an item by name."""
        self._items.pop(name, None)
