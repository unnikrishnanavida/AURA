"""Coordinator for the plugins subsystem."""

from __future__ import annotations

import logging
from typing import Any

from .exceptions import PluginsError
from .interfaces import PluginsProtocol
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry
from .plugin_validator import PluginValidator


class PluginsManager:
    """Manage plugin loading, registration, and execution."""

    def __init__(
        self,
        loader: PluginLoader | None = None,
        registry: PluginRegistry | None = None,
        validator: PluginValidator | None = None,
    ) -> None:
        self._loader = loader or PluginLoader()
        self._registry = registry or PluginRegistry()
        self._validator = validator or PluginValidator()
        self._logger = logging.getLogger("aura.plugins.manager")

    def register(self, name: str, plugin: PluginsProtocol) -> None:
        """Register a plugin instance under a unique name."""
        self._validator.validate(plugin)
        self._validator.validate_name(name)
        self._registry.register(name, plugin)
        self._logger.info("Registered plugin %s", name)

    def load_module(self, module_name: str, plugin_attr: str = "plugin") -> PluginsProtocol:
        """Load and register a plugin from an importable module."""
        plugin = self._loader.load_module(module_name, plugin_attr)
        self.register(getattr(plugin, "name", module_name), plugin)
        return plugin

    def load_from_path(self, path: str, plugin_attr: str = "plugin") -> PluginsProtocol:
        """Load and register a plugin from a filesystem path."""
        plugin = self._loader.load_from_path(path, plugin_attr)
        self.register(getattr(plugin, "name", path), plugin)
        return plugin

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered plugin by name."""
        plugin = self._registry.get(name)
        try:
            return plugin.execute(*args, **kwargs)
        except Exception as exc:
            raise PluginsError(f"Plugin '{name}' execution failed.") from exc

    def unregister(self, name: str) -> None:
        """Remove a plugin from the registry."""
        self._registry.unregister(name)
        self._logger.info("Unregistered plugin %s", name)

    def list(self) -> list[str]:
        """Return the list of registered plugin names."""
        return self._registry.list()

    def initialize_all(self) -> None:
        """Call initialize on all registered plugins."""
        for plugin in self._registry.values():
            if hasattr(plugin, "initialize"):
                try:
                    plugin.initialize()
                except Exception as exc:
                    self._logger.exception("Failed to initialize plugin: %s", exc)

    def shutdown_all(self) -> None:
        """Call shutdown on all registered plugins."""
        for plugin in self._registry.values():
            if hasattr(plugin, "shutdown"):
                try:
                    plugin.shutdown()
                except Exception as exc:
                    self._logger.exception("Failed to shutdown plugin: %s", exc)
