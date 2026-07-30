from __future__ import annotations

from typing import Dict, Any, Iterable


class ModuleRegistry:
    """Simple registry for loaded modules and metadata."""

    def __init__(self) -> None:
        self._modules: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, metadata: Dict[str, Any]) -> None:
        self._modules[name] = metadata

    def get(self, name: str) -> Dict[str, Any] | None:
        return self._modules.get(name)

    def list(self) -> Iterable[str]:
        return list(self._modules.keys())
