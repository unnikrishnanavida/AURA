"""Registry for capability definitions and their metadata."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class CapabilityRegistry:
    """Maintain capability registrations for the platform."""

    def __init__(self) -> None:
        self._capabilities: dict[str, RegistryEntry] = {}

    def register(self, name: str, description: str = "", *, tags: list[str] | None = None) -> RegistryEntry:
        """Register a new capability entry."""
        if name in self._capabilities:
            raise RegistryConflictError(f"Capability '{name}' is already registered.")
        metadata = RegistryMetadata(description=description, tags=tags or [])
        entry = RegistryEntry(name=name, kind="capability", data={"description": description}, metadata=metadata)
        self._capabilities[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a capability by name."""
        try:
            return self._capabilities[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Capability '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all registered capabilities."""
        return sorted(self._capabilities.values(), key=lambda item: item.name)
