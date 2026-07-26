"""
Kernel Registry

Maintains references to registered kernel components.
"""

from __future__ import annotations


class KernelRegistry:
    """Stores kernel components."""

    def __init__(self) -> None:
        self._components: dict[str, object] = {}

    def register(self, name: str, component: object) -> None:
        self._components[name] = component

    def resolve(self, name: str) -> object | None:
        return self._components.get(name)

    def unregister(self, name: str) -> None:
        self._components.pop(name, None)

    def clear(self) -> None:
        self._components.clear()

    @property
    def components(self) -> dict[str, object]:
        return dict(self._components)