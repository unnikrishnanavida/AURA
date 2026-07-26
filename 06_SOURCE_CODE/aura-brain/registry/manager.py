"""Coordinator for registry operations across the subsystem."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry
from .repository import InMemoryRegistryRepository


class RegistryManager:
    """High-level manager for organizing multiple registry repositories."""

    def __init__(self) -> None:
        self._repositories: dict[str, InMemoryRegistryRepository] = {}

    def create_repository(self, name: str) -> InMemoryRegistryRepository:
        """Create a repository for a registry namespace."""
        if name in self._repositories:
            raise RegistryConflictError(f"Repository '{name}' already exists.")
        repo = InMemoryRegistryRepository()
        self._repositories[name] = repo
        return repo

    def get_repository(self, name: str) -> InMemoryRegistryRepository:
        """Return a repository by namespace."""
        try:
            return self._repositories[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Repository '{name}' was not found.") from exc

    def register(self, repository_name: str, entry: RegistryEntry) -> None:
        """Register an entry in a named repository."""
        repo = self.get_repository(repository_name)
        repo.save(entry)

    def get(self, repository_name: str, entry_name: str) -> RegistryEntry:
        """Retrieve an entry from a repository."""
        return self.get_repository(repository_name).load(entry_name)

    def list(self, repository_name: str) -> list[RegistryEntry]:
        """List entries from a repository."""
        return self.get_repository(repository_name).all()

    def remove(self, repository_name: str, entry_name: str) -> None:
        """Remove an entry from a repository."""
        self.get_repository(repository_name).delete(entry_name)

    def namespaces(self) -> list[str]:
        """List repository namespaces."""
        return sorted(self._repositories)
