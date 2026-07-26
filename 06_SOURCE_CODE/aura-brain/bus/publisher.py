"""Publish events to the bus subsystem."""

from __future__ import annotations

import logging
from typing import Any

from .engine import BusEngine
from .events import BusEvent, BusEventBus


class Publisher:
    """Publish events into the bus event system."""

    def __init__(self, event_bus: BusEventBus | None = None, engine: BusEngine | None = None) -> None:
        self._event_bus = event_bus or BusEventBus()
        self._engine = engine or BusEngine(self._event_bus)
        self._logger = logging.getLogger("aura.bus.publisher")

    def publish(self, event_type: str, payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Publish an event to subscribed handlers."""
        event = BusEvent(type=event_type, payload=payload or {}, metadata=metadata or {})
        self._logger.debug("Publishing event %s", event_type)
        return self._event_bus.publish(event)

    def subscribe(self, event_type: str, listener: Any) -> None:
        """Subscribe a listener to an event type."""
        self._event_bus.subscribe(event_type, listener)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._event_bus.clear()
