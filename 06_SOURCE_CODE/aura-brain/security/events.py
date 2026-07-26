"""Event primitives for the security subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class SecurityEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class SecurityEventBus:
    """Minimal event bus for security events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[SecurityEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[SecurityEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: SecurityEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
