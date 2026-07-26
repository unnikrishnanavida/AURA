"""Monitoring manager exposing health and event capabilities."""

from __future__ import annotations

import logging
from typing import Any

from .engine import MonitoringEngine
from .exceptions import MonitoringError


class MonitoringManager:
    """Coordinate registration and execution of monitoring handlers."""

    def __init__(self, engine: MonitoringEngine | None = None) -> None:
        self._engine = engine or MonitoringEngine()
        self._logger = logging.getLogger("aura.monitoring.manager")

    def register_handler(self, name: str, handler: Any) -> None:
        """Register a monitoring handler for a named event."""
        self._engine.register(name, handler)
        self._logger.info("Registered monitoring handler %s", name)

    def publish_event(self, name: str, payload: Any = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Publish a monitoring event to subscribed handlers."""
        return self._engine.publish(name, payload, metadata or {})

    def execute(self, name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Execute a monitored handler directly."""
        return self._engine.execute(name, *args, **kwargs)

    def clear(self) -> None:
        """Remove all registered monitoring handlers."""
        self._engine.clear()
