"""Core implementation for the gateway subsystem."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .exceptions import GatewayError
from .validator import GatewayValidator

Handler = Callable[[dict[str, Any]], Any]


class Router:
    """Routes incoming gateway requests to named handlers."""

    def __init__(self, validator: GatewayValidator | None = None) -> None:
        self._routes: dict[str, Handler] = {}
        self._validator = validator or GatewayValidator()
        self._logger = logging.getLogger("aura.gateway.router")

    def register(self, route: str, handler: Handler) -> None:
        """Register a handler for a route."""
        self._validator.validate_route(route)
        if route in self._routes:
            raise GatewayError(f"Route '{route}' is already registered.")
        self._routes[route] = handler
        self._logger.info("Registered gateway route %s", route)

    def dispatch(self, route: str, request: dict[str, Any]) -> Any:
        """Dispatch an incoming request to the associated handler."""
        self._validator.validate_route(route)
        self._validator.validate_request(request)
        handler = self._routes.get(route)
        if handler is None:
            raise GatewayError(f"No route registered for '{route}'")
        return handler(request)

    def list(self) -> list[str]:
        """List registered route names."""
        return sorted(self._routes)

    def clear(self) -> None:
        """Remove all registered routes."""
        self._routes.clear()
