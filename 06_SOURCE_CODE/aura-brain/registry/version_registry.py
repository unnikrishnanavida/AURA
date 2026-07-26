"""Registry for versioned components and compatibility metadata."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class VersionRegistry:
    """Track versions of components and their compatibility."""

    def __init__(self) -> None:
        self._versions: dict[str, RegistryEntry] = {}

    def register(self, name: str, version: str, *, description: str = "") -> RegistryEntry:
        """Register a versioned component."""
        if name in self._versions:
            raise RegistryConflictError(f"Version entry '{name}' is already registered.")
        metadata = RegistryMetadata(version=version, description=description)
        entry = RegistryEntry(name=name, kind="version", data={"version": version}, metadata=metadata)
        self._versions[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a version entry."""
        try:
            return self._versions[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Version '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all version entries."""
        return sorted(self._versions.values(), key=lambda item: item.name)
