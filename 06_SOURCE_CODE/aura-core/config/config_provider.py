from __future__ import annotations

from typing import Dict, Any


class ConfigProvider:
    """Lightweight provider that merges multiple config sources."""

    def __init__(self, sources: list[Dict[str, Any]] | None = None) -> None:
        self.sources = list(sources or [])

    def provide(self) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for s in self.sources:
            merged.update(s)
        return merged
