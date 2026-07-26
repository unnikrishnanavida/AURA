"""Plugin validation helpers for the plugins subsystem."""

from __future__ import annotations

from typing import Any

from .exceptions import PluginsError
from .interfaces import PluginsProtocol


class PluginValidator:
    """Validate plugins before they are registered or executed."""

    def validate(self, plugin: Any) -> None:
        """Validate a plugin object implements the required protocol."""
        if not isinstance(plugin, PluginsProtocol):
            raise PluginsError("Plugin does not implement the required protocol.")
        if not callable(getattr(plugin, "execute", None)):
            raise PluginsError("Plugin must expose an execute() method.")

    def validate_name(self, name: str) -> None:
        """Validate plugin name conventions."""
        if not name or not name.strip():
            raise PluginsError("Plugin name cannot be empty.")
        if " " in name:
            raise PluginsError("Plugin name must not contain whitespace.")
