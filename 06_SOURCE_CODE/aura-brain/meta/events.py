"""Event primitives for the meta subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class MetaEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class MetaEventBus:
    """Minimal event bus for meta events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[MetaEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[MetaEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: MetaEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
