from __future__ import annotations

from typing import Dict, List

from .dependency_graph import DependencyGraph


class GraphBuilder:
    """Helper to build dependency graphs from descriptors."""

    def build(self, descriptors: Dict[str, List[str]]) -> DependencyGraph:
        g = DependencyGraph()
        for k, deps in descriptors.items():
            g.add_node(k, list(deps))
        return g
