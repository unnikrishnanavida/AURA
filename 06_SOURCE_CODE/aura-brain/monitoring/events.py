"""Event primitives for the monitoring subsystem."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class MonitoringEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class MonitoringEventBus:
    """Broadcast monitoring events to registered listeners."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[MonitoringEvent], Any]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[MonitoringEvent], Any]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def unsubscribe(self, event_type: str, listener: Callable[[MonitoringEvent], Any]) -> None:
        """Remove a listener from an event type."""
        if event_type in self._listeners:
            self._listeners[event_type] = [l for l in self._listeners[event_type] if l is not listener]

    def publish(self, event: MonitoringEvent) -> list[Any]:
        """Publish an event and return listener results."""
        results: list[Any] = []
        for listener in self._listeners.get(event.type, []):
            results.append(listener(event))
        return results

    def clear(self) -> None:
        """Clear all event listeners."""
        self._listeners.clear()
