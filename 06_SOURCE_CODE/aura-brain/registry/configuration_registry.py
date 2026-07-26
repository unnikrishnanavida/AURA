"""Registry for configuration profiles and their values."""

from __future__ import annotations

from typing import Any

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class ConfigurationRegistry:
    """Store configuration entries keyed by logical configuration name."""

    def __init__(self) -> None:
        self._configurations: dict[str, RegistryEntry] = {}

    def register(self, name: str, values: dict[str, Any], *, description: str = "") -> RegistryEntry:
        """Register a configuration entry."""
        if name in self._configurations:
            raise RegistryConflictError(f"Configuration '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="configuration", data=values, metadata=metadata)
        self._configurations[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Get a configuration entry by name."""
        try:
            return self._configurations[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Configuration '{name}' was not found.") from exc

    def update(self, name: str, values: dict[str, Any]) -> RegistryEntry:
        """Update an existing configuration payload."""
        entry = self.get(name)
        entry.data.update(values)
        return entry

    def list(self) -> list[RegistryEntry]:
        """List all registered configurations."""
        return sorted(self._configurations.values(), key=lambda item: item.name)
