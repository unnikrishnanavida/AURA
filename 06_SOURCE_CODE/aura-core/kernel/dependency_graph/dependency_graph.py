from __future__ import annotations

from typing import Dict, List


class DependencyGraph:
    """Graph representation for modules and their dependencies."""

    def __init__(self) -> None:
        self._deps: Dict[str, List[str]] = {}

    def add_node(self, name: str, dependencies: List[str] | None = None) -> None:
        self._deps[name] = dependencies or []

    def nodes(self):
        return list(self._deps.keys())

    def edges(self):
        return dict(self._deps)
