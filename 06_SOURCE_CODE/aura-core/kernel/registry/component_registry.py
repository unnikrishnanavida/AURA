from __future__ import annotations

from typing import Dict, Any, Iterable


class ComponentRegistry:
    """Registry for in-memory components keyed by name."""

    def __init__(self) -> None:
        self._components: Dict[str, Any] = {}

    def register(self, name: str, component: Any) -> None:
        self._components[name] = component

    def get(self, name: str):
        return self._components.get(name)

    def list(self) -> Iterable[str]:
        return list(self._components.keys())
