"""Discovery helpers for scanning Python packages and modules."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable


class DiscoveryService:
    """Discover Python modules and packages from an import path."""

    def discover(self, package_name: str, predicate: Callable[[str], bool] | None = None) -> list[str]:
        """Return discovered module names for a given package."""
        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            return []

        discovered: list[str] = []
        for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            module_name = module_info.name
            if predicate is None or predicate(module_name):
                discovered.append(module_name)
        return sorted(discovered)

    def load_module(self, module_name: str):
        """Import a module and return it."""
        return importlib.import_module(module_name)
