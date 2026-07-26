"""Core implementation for the bus subsystem."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .engine import BusEngine
from .events import BusEvent


class Dispatcher:
    """Dispatch bus events through registered handler chains."""

    def __init__(self, engine: BusEngine | None = None) -> None:
        self._engine = engine or BusEngine()
        self._logger = logging.getLogger("aura.bus.dispatcher")

    def register(self, event_type: str, handler: Callable[[BusEvent], Any]) -> None:
        """Register an event handler."""
        self._engine.register(event_type, handler)

    def dispatch(self, event_type: str, payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Dispatch an event through the engine."""
        self._logger.debug("Dispatching event %s", event_type)
        return self._engine.publish(event_type, payload or {}, metadata or {})

    def clear(self) -> None:
        """Clear dispatcher state."""
        self._engine.clear()
