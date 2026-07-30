from __future__ import annotations

from typing import Dict, List, Any

from .dependency_resolver import DependencyResolver
from .import_manager import ImportManager


class ModuleLoader:
    """Load modules in dependency order and expose module metadata."""

    def __init__(self) -> None:
        self._importer = ImportManager()
        self._resolver = DependencyResolver()
        self._modules: Dict[str, Any] = {}

    def load(self, modules: Dict[str, List[str]]) -> List[str]:
        order = self._resolver.resolve(modules)
        for name in order:
            self._modules[name] = self._importer.import_module(name)
        return order

    def get(self, name: str) -> Any:
        return self._modules.get(name)
