"""Base plugin implementation for the plugins subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .interfaces import PluginsProtocol


@dataclass(slots=True)
class Plugin(PluginsProtocol):
    """Simple plugin model that implements the plugin contract."""

    name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the plugin logic."""
        raise NotImplementedError("Plugin.execute() must be implemented by subclasses.")
