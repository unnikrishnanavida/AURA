from __future__ import annotations

from typing import Any, Dict

from .config_loader import ConfigLoader


class ConfigManager:
    """Facade to load and provide configuration for components."""

    def __init__(self, loader: ConfigLoader) -> None:
        self._loader = loader
        self._config: Dict[str, Any] = {}

    def load(self) -> None:
        self._config = self._loader.load()

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._config)
