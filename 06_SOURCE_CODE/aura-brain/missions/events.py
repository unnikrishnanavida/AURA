"""Event primitives for the missions subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class MissionsEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class MissionsEventBus:
    """Minimal event bus for missions events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[MissionsEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[MissionsEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: MissionsEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
