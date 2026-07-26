"""Event primitives for the plugins subsystem."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class PluginsEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class PluginsEventBus:
    """Broadcast events to subscribed listeners."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[PluginsEvent], Any]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[PluginsEvent], Any]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def unsubscribe(self, event_type: str, listener: Callable[[PluginsEvent], Any]) -> None:
        """Unregister a listener for an event type."""
        if event_type in self._listeners:
            self._listeners[event_type] = [l for l in self._listeners[event_type] if l is not listener]

    def publish(self, event: PluginsEvent) -> list[Any]:
        """Publish an event and return listener results."""
        results: list[Any] = []
        for listener in self._listeners.get(event.type, []):
            results.append(listener(event))
        return results

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._listeners.clear()
