"""Utility helpers for loading registry-backed components dynamically."""

from __future__ import annotations

import importlib
from typing import Any


class RegistryLoader:
    """Load classes or callables from dotted import paths."""

    def load(self, dotted_path: str) -> Any:
        """Import an object from a dotted path."""
        module_name, _, attr_name = dotted_path.rpartition(".")
        if not module_name or not attr_name:
            raise ValueError(f"Invalid dotted path: {dotted_path}")
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)

    def instantiate(self, dotted_path: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate an importable class from a dotted path."""
        obj = self.load(dotted_path)
        return obj(*args, **kwargs)
