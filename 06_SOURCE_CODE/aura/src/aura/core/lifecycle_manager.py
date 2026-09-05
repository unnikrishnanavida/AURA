"""Lifecycle management.

Starts components respecting their declared dependency order (topological
sort with cycle detection) and stops them in reverse. If a component fails to
start, every already-started component is stopped and a LifecycleError with a
partial-start snapshot describes the failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.core.registry import ComponentRegistry
from aura.foundation.errors import LifecycleError
from aura.foundation.lifecycle import Component


@dataclass
class LifecycleSnapshot:
    started: list[str] = field(default_factory=list)
    failed: str | None = None
    reason: str | None = None


class LifecycleManager:
    """Orchestrates start/stop across registered :class:`Component`s."""

    def __init__(self, registry: ComponentRegistry) -> None:
        self._registry = registry
        self._started: list[str] = []
        self._failed: str | None = None
        self._failure_reason: str | None = None
        self._shutdown_errors: list[str] = []

    @property
    def shutdown_errors(self) -> list[str]:
        return list(self._shutdown_errors)

    def _ordered(self) -> list[str]:
        names = set(self._registry.names())
        order: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise LifecycleError(f"circular component dependency involving {name}")
            visiting.add(name)
            for dep in self._registry.dependencies(name):
                if dep in names:
                    visit(dep)
            visiting.discard(name)
            visited.add(name)
            order.append(name)

        for name in sorted(names):
            visit(name)
        return order

    def start_all(self) -> LifecycleSnapshot:
        for name in self._ordered():
            component = self._registry.get(name)
            if not isinstance(component, Component):
                raise LifecycleError(f"component {name!r} does not implement Component")
            try:
                component.start()
            except Exception as exc:  # component-specific startup failure
                self._failed = name
                self._failure_reason = str(exc)
                self._stop_started()
                return self.snapshot()
            self._started.append(name)
        return self.snapshot()

    def stop_all(self) -> None:
        self._stop_started()
        self._started = []
        self._failed = None

    def _stop_started(self) -> None:
        for name in reversed(self._started):
            component = self._registry.get(name)
            if not isinstance(component, Component):
                continue
            try:
                component.stop()
            except Exception as exc:  # never let shutdown failure mask startup failure
                self._shutdown_errors.append(f"{name}: {exc}")

    @property
    def is_running(self) -> bool:
        return self._failed is None and len(self._started) == len(self._registry.names())

    def started(self) -> list[str]:
        return list(self._started)

    def snapshot(self) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            started=list(self._started), failed=self._failed, reason=self._failure_reason
        )


__all__ = ["LifecycleManager", "LifecycleSnapshot"]