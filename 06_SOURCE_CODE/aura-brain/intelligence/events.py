"""Event primitives for the intelligence subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class IntelligenceEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class IntelligenceEventBus:
    """Minimal event bus for intelligence events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[IntelligenceEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[IntelligenceEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: IntelligenceEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
