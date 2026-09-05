"""Cognitive memory graph.

Memories link through causality, similarity, temporal sequence, shared goals,
and shared outcomes. The graph is derived from explicit entries and supports
traversal for consolidation, planning, and understanding.
"""

from __future__ import annotations

from typing import Any

from aura.foundation.ids import MemoryId
from aura.memory.models import LinkKind, MemoryEntry


class MemoryGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._links: dict[str, dict[str, LinkKind]] = {}

    def register(self, entry: MemoryEntry) -> None:
        self._nodes[str(entry.id)] = {"key": entry.key, "kind": entry.kind}

    def link(self, source: MemoryEntry, target: MemoryEntry, kind: LinkKind) -> None:
        self.register(source)
        self.register(target)
        self._links.setdefault(str(source.id), {})[str(target.id)] = kind
        self._links.setdefault(str(target.id), {})[str(source.id)] = kind

    def neighbors(self, memory_id: MemoryId) -> list[MemoryId]:
        return [MemoryId(mid.split("-", 1)[-1]) for mid in self._links.get(str(memory_id), {})]

    def expand(self, memory_id: MemoryId, *, depth: int = 1) -> list[MemoryId]:
        frontier = [str(memory_id)]
        seen: set[str] = {str(memory_id)}
        for _ in range(max(0, depth)):
            nxt: list[str] = []
            for current in frontier:
                for neighbor in self._links.get(current, {}):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        nxt.append(neighbor)
            frontier = nxt
        return [MemoryId(s.split("-", 1)[-1]) for s in seen if s != str(memory_id)]

    def node_count(self) -> int:
        return len(self._nodes)

    def link_count(self) -> int:
        return sum(len(v) for v in self._links.values()) // 2


__all__ = ["MemoryGraph"]