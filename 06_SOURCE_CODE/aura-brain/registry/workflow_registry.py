"""Registry for workflows and their associated steps."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryMetadata


class WorkflowRegistry:
    """Register workflows used by the orchestration layer."""

    def __init__(self) -> None:
        self._workflows: dict[str, RegistryEntry] = {}

    def register(self, name: str, steps: list[str], *, description: str = "") -> RegistryEntry:
        """Register a workflow entry."""
        if name in self._workflows:
            raise RegistryConflictError(f"Workflow '{name}' is already registered.")
        metadata = RegistryMetadata(description=description)
        entry = RegistryEntry(name=name, kind="workflow", data={"steps": steps}, metadata=metadata)
        self._workflows[name] = entry
        return entry

    def get(self, name: str) -> RegistryEntry:
        """Retrieve a workflow entry."""
        try:
            return self._workflows[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Workflow '{name}' was not found.") from exc

    def list(self) -> list[RegistryEntry]:
        """Return all workflow entries."""
        return sorted(self._workflows.values(), key=lambda item: item.name)
