"""Execution engine for the plugins subsystem."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .events import PluginsEvent, PluginsEventBus
from .interfaces import PluginsProtocol
from .exceptions import PluginsError

Handler = Callable[..., Any]


class PluginsEngine:
    """Coordinate execution operations for plugins."""

    def __init__(self, event_bus: PluginsEventBus | None = None) -> None:
        self._plugins: dict[str, PluginsProtocol] = {}
        self._event_bus = event_bus or PluginsEventBus()
        self._logger = logging.getLogger("aura.plugins")

    def register(self, name: str, plugin: PluginsProtocol) -> None:
        """Register a plugin instance for execution."""
        if not isinstance(plugin, PluginsProtocol):
            raise PluginsError("Plugin must implement PluginsProtocol")
        self._plugins[name] = plugin
        self._logger.info("Registered plugin %s", name)

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered plugin."""
        plugin = self._plugins.get(name)
        if plugin is None:
            raise PluginsError(f"Plugin '{name}' is not registered.")
        return plugin.execute(*args, **kwargs)

    def trigger(self, event_type: str, payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Trigger a plugin event."""
        event = PluginsEvent(type=event_type, payload=payload or {}, metadata=metadata or {})
        self._logger.debug("Triggering plugin event %s", event_type)
        return self._event_bus.publish(event)

    def subscribe(self, event_type: str, listener: Handler) -> None:
        """Subscribe to plugin events."""
        self._event_bus.subscribe(event_type, listener)

    def clear(self) -> None:
        """Clear all plugins and event handlers."""
        self._plugins.clear()
        self._event_bus.clear()
