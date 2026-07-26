"""Event primitives for the innovation subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class InnovationEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class InnovationEventBus:
    """Minimal event bus for innovation events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[InnovationEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[InnovationEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: InnovationEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
