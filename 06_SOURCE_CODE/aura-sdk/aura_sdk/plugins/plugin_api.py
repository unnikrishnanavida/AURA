"""AURA SDK Plugins plugin_api."""

from __future__ import annotations
from typing import Any


class PluginApi:
    """Core plugin API for aura_sdk.plugins."""

    def __init__(self) -> None:
        self.registry: dict[str, Any] = {}

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize plugin runtime state."""
        self.config = config or {}

    def register(self, name: str, provider: Any) -> None:
        """Register a provider or capability with the plugin API."""
        if not name:
            raise ValueError("name must be provided")
        self.registry[name] = provider

    def get(self, name: str, default: Any | None = None) -> Any:
        """Return a registered plugin provider."""
        return self.registry.get(name, default)

    def shutdown(self) -> None:
        """Clear plugin registry state."""
        self.registry.clear()
