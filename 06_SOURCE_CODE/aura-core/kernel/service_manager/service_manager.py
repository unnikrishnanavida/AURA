from __future__ import annotations

from typing import Dict, Any
from .service_descriptor import ServiceDescriptor
from .service_loader import ServiceLoader


class ServiceManager:
    """High-level service manager that coordinates registry and loader."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, ServiceDescriptor] = {}
        self._loader = ServiceLoader()

    def register(self, descriptor: ServiceDescriptor) -> None:
        self._descriptors[descriptor.name] = descriptor

    def get(self, name: str) -> Any:
        desc = self._descriptors.get(name)
        if not desc:
            raise KeyError(name)
        return self._loader.load(desc)
