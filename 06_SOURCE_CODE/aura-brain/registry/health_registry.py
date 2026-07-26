"""Health registry for tracking component health state."""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import RegistryConflictError, RegistryNotFoundError


@dataclass(slots=True)
class ComponentHealth:
    """Represents health information for a registry-backed component."""

    name: str
    healthy: bool
    message: str = ""


class HealthRegistry:
    """Track health of registered components."""

    def __init__(self) -> None:
        self._health: dict[str, ComponentHealth] = {}

    def register(self, health: ComponentHealth) -> None:
        """Register or update component health."""
        if health.name in self._health:
            raise RegistryConflictError(f"Health record '{health.name}' already exists.")
        self._health[health.name] = health

    def update(self, health: ComponentHealth) -> ComponentHealth:
        """Update an existing health record."""
        self._health[health.name] = health
        return health

    def get(self, name: str) -> ComponentHealth:
        """Retrieve the health record for a component."""
        try:
            return self._health[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Health for '{name}' was not found.") from exc

    def list(self) -> list[ComponentHealth]:
        """List all health records."""
        return sorted(self._health.values(), key=lambda item: item.name)
