"""Registry for engine implementations."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class EngineRegistry:
    """Register engine implementations by logical name."""

    def __init__(self) -> None:
        self._engines: dict[str, RegistryEntry] = {}

    def register(self, name: str, engine_type: str, *, description: str = "") -> RegistryEntry:
        """Register a new engine."""
        if name in self._engines:
            raise RegistryConflictError(f"Engine '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="engine", data={"engine_type": engine_type}, metadata=metadata)
        self._engines[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve an engine entry."""
        try:
            return self._engines[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Engine '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all registered engines."""
        return sorted(self._engines.values(), key=lambda item: item.name)
