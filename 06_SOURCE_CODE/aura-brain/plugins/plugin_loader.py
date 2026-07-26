"""Plugin discovery and loading helpers."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Any

from .exceptions import PluginsError
from .interfaces import PluginsProtocol


class PluginLoader:
    """Load plugin modules from disk or package imports."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("aura.plugins.loader")

    def load_module(self, module_name: str, plugin_attr: str = "plugin") -> PluginsProtocol:
        """Load a plugin from a Python module."""
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise PluginsError(f"Cannot import module '{module_name}'") from exc

        plugin = getattr(module, plugin_attr, None)
        if plugin is None:
            raise PluginsError(f"Module '{module_name}' does not expose '{plugin_attr}'")
        if not isinstance(plugin, PluginsProtocol):
            raise PluginsError("Loaded object does not implement PluginsProtocol")
        return plugin

    def load_from_path(self, path: str, plugin_attr: str = "plugin") -> PluginsProtocol:
        """Load a plugin from a filesystem path."""
        source = Path(path)
        if not source.exists():
            raise PluginsError(f"Plugin path '{path}' does not exist.")

        module_name = source.stem
        spec = importlib.util.spec_from_file_location(module_name, str(source))
        if spec is None or spec.loader is None:
            raise PluginsError(f"Cannot load plugin file {path}")

        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        plugin = getattr(module, plugin_attr, None)
        if plugin is None:
            raise PluginsError(f"Plugin file '{path}' does not expose '{plugin_attr}'")
        if not isinstance(plugin, PluginsProtocol):
            raise PluginsError("Loaded object does not implement PluginsProtocol")
        return plugin
