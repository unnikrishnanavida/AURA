"""Loader helpers for the config subsystem."""

from __future__ import annotations

from importlib import import_module
from typing import Any


class ConfigLoader:
    """Load implementations by dotted path."""

    def load(self, dotted_path: str) -> Any:
        """Import and return an object."""
        module_name, _, attribute = dotted_path.rpartition('.')
        if not module_name or not attribute:
            raise ValueError(f'Invalid dotted path: {dotted_path}')
        module = import_module(module_name)
        return getattr(module, attribute)
