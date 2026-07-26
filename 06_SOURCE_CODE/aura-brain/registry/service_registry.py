"""Registry for services provided by the platform."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class ServiceRegistry:
    """Register services with optional endpoint metadata."""

    def __init__(self) -> None:
        self._services: dict[str, RegistryEntry] = {}

    def register(self, name: str, endpoint: str, *, description: str = "") -> RegistryEntry:
        """Register a service entry."""
        if name in self._services:
            raise RegistryConflictError(f"Service '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="service", data={"endpoint": endpoint}, metadata=metadata)
        self._services[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a service entry."""
        try:
            return self._services[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Service '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all registered services."""
        return sorted(self._services.values(), key=lambda item: item.name)
