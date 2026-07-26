"""Execution engine for the bus subsystem."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .events import BusEvent, BusEventBus
from .exceptions import BusError

Handler = Callable[[BusEvent], Any]
Middleware = Callable[[BusEvent, Callable[[BusEvent], Any]], Any]


class BusEngine:
    """Coordinate execution operations for bus."""

    def __init__(self, event_bus: BusEventBus | None = None) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self._middleware: list[Middleware] = []
        self._event_bus = event_bus or BusEventBus()
        self._logger = logging.getLogger("aura.bus")

    def register(self, name: str, handler: Handler) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(name, []).append(handler)
        self._event_bus.subscribe(name, handler)

    def register_middleware(self, middleware: Middleware) -> None:
        """Register middleware around event dispatch."""
        self._middleware.append(middleware)

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a named handler directly."""
        if name not in self._handlers:
            raise BusError(f"No handler registered for: {name}")
        results = []
        for handler in self._handlers[name]:
            results.append(handler(*args, **kwargs))
        return results

    def publish(self, event_type: str, payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Create and publish an event to subscribed handlers."""
        event = BusEvent(type=event_type, payload=payload or {}, metadata=metadata or {})
        self._logger.debug("Publishing event %s with payload %s", event.type, event.payload)
        return self._dispatch(event)

    def _dispatch(self, event: BusEvent) -> list[Any]:
        def call_target(evt: BusEvent) -> list[Any]:
            return self._event_bus.publish(evt)

        if not self._middleware:
            return call_target(event)

        result: list[Any] = []
        next_fn = call_target
        for middleware in reversed(self._middleware):
            prior = next_fn

            def make_next(mw: Middleware, next_fn: Callable[[BusEvent], list[Any]]) -> Callable[[BusEvent], list[Any]]:
                return lambda e: mw(e, next_fn)

            next_fn = make_next(middleware, prior)
        return next_fn(event)

    def clear(self) -> None:
        """Clear handlers and middleware."""
        self._handlers.clear()
        self._middleware.clear()
        self._event_bus.clear()
