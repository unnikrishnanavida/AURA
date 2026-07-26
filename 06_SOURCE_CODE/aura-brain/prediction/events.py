"""Event primitives for the prediction subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class PredictionEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class PredictionEventBus:
    """Minimal event bus for prediction events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[PredictionEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[PredictionEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: PredictionEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
