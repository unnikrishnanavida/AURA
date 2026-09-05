"""Service registry for aura-core.

Explicit instance-based registry (NO hidden module-global state): each
registry owns its namespace, so multiple kernels/components can coexist with
deterministic behavior.
"""

from __future__ import annotations

from typing import Any


class ServiceRegistry:
    """An instance-scoped registry binding service names to instances."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        return self._services.get(name)

    def require(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"service {name!r} is not registered")
        return self._services[name]

    def unregister(self, name: str) -> Any | None:
        return self._services.pop(name, None)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))

    def clear(self) -> None:
        self._services.clear()

    def __contains__(self, name: str) -> bool:
        return name in self._services


__all__ = ["ServiceRegistry"]