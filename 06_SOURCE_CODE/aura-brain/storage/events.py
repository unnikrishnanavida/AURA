"""Event primitives for the storage subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class StorageEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class StorageEventBus:
    """Minimal event bus for storage events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[StorageEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[StorageEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: StorageEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
