"""Provenance.

The provenance graph reconstructs causal chains from flight-recorder events.
An event may declare its cause through the reserved payload key ``caused_by``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aura.foundation.ids import EventId
from aura.observability.flight_recorder import EventRecord

CAUSED_BY = "caused_by"


@dataclass(frozen=True)
class ProvenanceNode:
    event: EventRecord
    parents: tuple[EventId, ...] = ()
    children: tuple[EventId, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event.event_id),
            "parents": [str(p) for p in self.parents],
            "children": [str(c) for c in self.children],
            "event_type": self.event.event_type,
        }


class ProvenanceGraph:
    """Directed acyclic graph of causation derived from recorded events."""

    def __init__(self) -> None:
        self._nodes: dict[str, ProvenanceNode] = {}
        self._edges: dict[str, list[str]] = {}

    def ingest(self, event: EventRecord) -> None:
        key = str(event.event_id)
        if key in self._nodes:
            return
        parents: list[EventId] = []
        for parent_raw in event.payload.get(CAUSED_BY, []) or []:
            parent_id = EventId.from_str(str(parent_raw))
            parents.append(parent_id)
            self._edges.setdefault(str(parent_id), []).append(key)
        self._nodes[key] = ProvenanceNode(event=event, parents=tuple(parents))

    def load(self, events: list[EventRecord]) -> None:
        for event in sorted(events, key=lambda e: e.sequence):
            self.ingest(event)

    def node(self, event_id: EventId | str) -> ProvenanceNode | None:
        return self._nodes.get(str(event_id))

    def path_to(self, event_id: EventId | str) -> list[ProvenanceNode]:
        """Return the ancestor chain (cause path) for an event, root first."""
        key = str(event_id)
        chain: list[ProvenanceNode] = []
        visited: set[str] = set()
        node = self._nodes.get(key)
        while node is not None and key not in visited:
            visited.add(key)
            chain.append(node)
            parents = node.parents
            if not parents:
                break
            key = str(parents[0])
            node = self._nodes.get(key)
        return list(reversed(chain))

    def explain(self, event_id: EventId | str) -> dict[str, Any]:
        path = self.path_to(event_id)
        return {
            "target": str(event_id),
            "cause_chain": [
                {
                    "event_id": str(n.event.event_id),
                    "event_type": n.event.event_type,
                    "source": n.event.source,
                }
                for n in path
            ],
        }

    def nodes(self) -> list[ProvenanceNode]:
        return sorted(self._nodes.values(), key=lambda n: n.event.sequence)


__all__ = ["ProvenanceGraph"]