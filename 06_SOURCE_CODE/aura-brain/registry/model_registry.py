"""Registry for model definitions used across the platform."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class ModelRegistry:
    """Register models by name and kind."""

    def __init__(self) -> None:
        self._models: dict[str, RegistryEntry] = {}

    def register(self, name: str, model_type: str, *, description: str = "") -> RegistryEntry:
        """Register a new model entry."""
        if name in self._models:
            raise RegistryConflictError(f"Model '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="model", data={"model_type": model_type}, metadata=metadata)
        self._models[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a model entry."""
        try:
            return self._models[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Model '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all model entries."""
        return sorted(self._models.values(), key=lambda item: item.name)
