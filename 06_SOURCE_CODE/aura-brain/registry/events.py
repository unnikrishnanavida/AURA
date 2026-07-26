"""Registry event definitions and a simple event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class RegistryEvent:
    """A registry-related event emitted by the system."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class RegistryEventBus:
    """A minimal event bus for registry events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[RegistryEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[RegistryEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: RegistryEvent) -> None:
        """Publish an event to all listeners of that type."""
        for listener in self._listeners.get(event.type, []):
            listener(event)

    def clear(self) -> None:
        """Remove all registered listeners."""
        self._listeners.clear()
