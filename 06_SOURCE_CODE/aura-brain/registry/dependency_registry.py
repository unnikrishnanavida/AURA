"""Registry for dependency relationships between components."""

from __future__ import annotations

from collections import defaultdict

from .exceptions import RegistryConflictError, RegistryNotFoundError


class DependencyRegistry:
    """Track directed dependencies between registered entities."""

    def __init__(self) -> None:
        self._dependencies: dict[str, set[str]] = defaultdict(set)

    def add_dependency(self, source: str, dependency: str) -> None:
        """Record a dependency from one component to another."""
        if source == dependency:
            raise RegistryConflictError("A component cannot depend on itself.")
        self._dependencies[source].add(dependency)

    def remove_dependency(self, source: str, dependency: str) -> None:
        """Remove a dependency edge."""
        if source in self._dependencies:
            self._dependencies[source].discard(dependency)

    def dependencies_for(self, source: str) -> list[str]:
        """Return all dependencies for a component."""
        return sorted(self._dependencies.get(source, set()))

    def dependents_for(self, dependency: str) -> list[str]:
        """Return all components that depend on the given component."""
        return sorted(
            source
            for source, targets in self._dependencies.items()
            if dependency in targets
        )

    def resolve(self, source: str) -> list[str]:
        """Return the transitive closure of dependencies for the given source."""
        visited: set[str] = set()
        stack = list(self.dependencies_for(source))
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.dependencies_for(current))
        return sorted(visited)

    def get_all(self) -> dict[str, list[str]]:
        """Return the complete dependency graph."""
        return {name: sorted(targets) for name, targets in self._dependencies.items()}

    def clear(self) -> None:
        """Clear all registered dependencies."""
        self._dependencies.clear()
