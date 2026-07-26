"""Plugin registry for storing loaded plugin instances."""

from __future__ import annotations

from typing import Dict

from .exceptions import PluginsError
from .interfaces import PluginsProtocol


class PluginRegistry:
    """Tracks loaded plugins by unique name."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginsProtocol] = {}

    def register(self, name: str, plugin: PluginsProtocol) -> None:
        """Register a plugin instance under a unique name."""
        if name in self._plugins:
            raise PluginsError(f"Plugin '{name}' is already registered.")
        self._plugins[name] = plugin

    def get(self, name: str) -> PluginsProtocol:
        """Retrieve a registered plugin by name."""
        plugin = self._plugins.get(name)
        if plugin is None:
            raise PluginsError(f"Plugin '{name}' is not registered.")
        return plugin

    def list(self) -> list[str]:
        """List registered plugin names."""
        return sorted(self._plugins)

    def values(self) -> list[PluginsProtocol]:
        """Return all registered plugin instances."""
        return list(self._plugins.values())

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name."""
        self._plugins.pop(name, None)

    def clear(self) -> None:
        """Remove all registered plugins."""
        self._plugins.clear()
