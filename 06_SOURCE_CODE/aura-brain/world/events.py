"""Event primitives for the world subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class WorldEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class WorldEventBus:
    """Minimal event bus for world events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[WorldEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[WorldEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: WorldEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
