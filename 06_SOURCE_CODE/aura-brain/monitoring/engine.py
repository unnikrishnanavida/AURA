"""Execution engine for the monitoring subsystem."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .events import MonitoringEvent, MonitoringEventBus
from .exceptions import MonitoringError

Handler = Callable[[Any], Any]


class MonitoringEngine:
    """Coordinate execution operations for monitoring."""

    def __init__(self, event_bus: MonitoringEventBus | None = None) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self._event_bus = event_bus or MonitoringEventBus()
        self._logger = logging.getLogger("aura.monitoring")

    def register(self, name: str, handler: Handler) -> None:
        """Register a handler for a monitoring event."""
        self._handlers.setdefault(name, []).append(handler)
        self._event_bus.subscribe(name, handler)

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered handler directly."""
        handlers = self._handlers.get(name)
        if not handlers:
            raise MonitoringError(f"No monitoring handler registered for '{name}'")
        return [handler(*args, **kwargs) for handler in handlers]

    def publish(self, name: str, payload: Any = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Publish a monitoring event."""
        event = MonitoringEvent(type=name, payload=payload, metadata=metadata or {})
        self._logger.debug("Publishing monitoring event %s", name)
        return self._event_bus.publish(event)

    def clear(self) -> None:
        """Clear all registered handlers and subscriptions."""
        self._handlers.clear()
        self._event_bus.clear()
