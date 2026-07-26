"""Registry for plugin implementations and their metadata."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class PluginRegistry:
    """Maintain plugin registrations for extensibility."""

    def __init__(self) -> None:
        self._plugins: dict[str, RegistryEntry] = {}

    def register(self, name: str, plugin_type: str, *, description: str = "") -> RegistryEntry:
        """Register a plugin entry."""
        if name in self._plugins:
            raise RegistryConflictError(f"Plugin '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="plugin", data={"plugin_type": plugin_type}, metadata=metadata)
        self._plugins[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a plugin entry."""
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Plugin '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all plugin entries."""
        return sorted(self._plugins.values(), key=lambda item: item.name)
