from __future__ import annotations

from typing import Dict, Any, Iterable


class ServiceRegistry:
    """Registry for available services and descriptors."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}

    def register(self, name: str, descriptor: Any) -> None:
        self._services[name] = descriptor

    def get(self, name: str) -> Any | None:
        return self._services.get(name)

    def list(self) -> Iterable[str]:
        return list(self._services.keys())
