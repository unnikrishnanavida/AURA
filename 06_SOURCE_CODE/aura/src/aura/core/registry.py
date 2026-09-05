"""Component registry.

A named, dependency-aware registry for AURA services. Engines register their
public services here so the lifecycle manager and health aggregator can manage
them uniformly. Registration is explicit (no magic import discovery) to keep
startup deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from aura.foundation.errors import LifecycleError, NotFoundError

T = TypeVar("T")


@dataclass(frozen=True)
class ComponentEntry(Generic[T]):
    name: str
    component: T
    dependencies: tuple[str, ...] = ()


class ComponentRegistry:
    """Stores components by unique name with their declared dependencies."""

    def __init__(self) -> None:
        self._entries: dict[str, ComponentEntry[object]] = {}

    def register(self, name: str, component: object, *, dependencies: tuple[str, ...] = ()) -> None:
        if not name:
            raise LifecycleError("component name must not be empty")
        if name in self._entries:
            raise LifecycleError(f"component already registered: {name}")
        self._entries[name] = ComponentEntry(name=name, component=component, dependencies=dependencies)

    def get(self, name: str) -> object:
        if name not in self._entries:
            raise NotFoundError(f"component not registered: {name}")
        return self._entries[name].component

    def has(self, name: str) -> bool:
        return name in self._entries

    def dependencies(self, name: str) -> tuple[str, ...]:
        return self._entries[name].dependencies

    def names(self) -> list[str]:
        return sorted(self._entries)

    def all(self) -> dict[str, object]:
        return {k: e.component for k, e in self._entries.items()}

    def validate_graph(self) -> list[str]:
        """Return any dependency names that reference unknown components."""
        bad = [
            d
            for entry in self._entries.values()
            for d in entry.dependencies
            if d not in self._entries
        ]
        return sorted(set(bad))


__all__ = ["ComponentRegistry"]