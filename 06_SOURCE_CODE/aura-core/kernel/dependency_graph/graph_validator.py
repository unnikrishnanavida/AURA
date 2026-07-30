from __future__ import annotations

from typing import Dict, List


class GraphValidationError(Exception):
    pass


class GraphValidator:
    """Validate a dependency graph for cycles using DFS."""

    def validate(self, graph: Dict[str, List[str]]) -> None:
        visited = {}

        def visit(node: str) -> None:
            if visited.get(node) == 1:
                raise GraphValidationError(f"Cycle detected at {node}")
            if visited.get(node) == 2:
                return
            visited[node] = 1
            for n in graph.get(node, []):
                visit(n)
            visited[node] = 2

        for n in graph:
            if visited.get(n) is None:
                visit(n)
