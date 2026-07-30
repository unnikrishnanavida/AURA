from __future__ import annotations

from typing import Callable, Dict, Any

from .service_descriptor import ServiceDescriptor


class ServiceLoader:
    """Loads service instances from descriptors with simple lifetime management."""

    def __init__(self) -> None:
        self._singletons: Dict[str, Any] = {}

    def load(self, descriptor: ServiceDescriptor) -> Any:
        if descriptor.singleton:
            if descriptor.name not in self._singletons:
                self._singletons[descriptor.name] = descriptor.factory()
            return self._singletons[descriptor.name]
        return descriptor.factory()
