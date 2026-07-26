"""Core implementation for the bus subsystem."""

from __future__ import annotations

from typing import Any, Callable

from .events import BusEvent, BusEventBus


class Subscriber:
    """Subscribe listeners to bus events."""

    def __init__(self, event_bus: BusEventBus | None = None) -> None:
        self._event_bus = event_bus or BusEventBus()
        self._listeners: dict[str, list[Callable[[BusEvent], Any]]] = {}

    def register(self, event_type: str, listener: Callable[[BusEvent], Any]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)
        self._event_bus.subscribe(event_type, listener)

    def list(self) -> list[str]:
        """Return registered event types."""
        return sorted(self._listeners)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._listeners.clear()
        self._event_bus.clear()
