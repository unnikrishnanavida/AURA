"""Provenance engine: reconstructs why an outcome happened.

Provenance answers "why was this action selected / what caused this result?"
The provenance graph is derived deterministically from the flight recorder's
event stream; it stores nothing of its own so it cannot drift from observed
history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura_agent.flight_recorder.agent_flight_recorder import AgentFlightRecorder
from aura_agent.flight_recorder.events.agent_event import AgentEvent

__all__ = [
    "ProvenanceNode",
    "ProvenanceLink",
    "ProvenanceGraph",
    "ProvenanceEngine",
]


@dataclass(frozen=True)
class ProvenanceNode:
    """A single event in the provenance chain."""

    event_id: str
    event_type: str
    payload: dict
    timestamp: str = ""  # ISO timestamp from the recorded AgentEvent


@dataclass(frozen=True)
class ProvenanceLink:
    """A causal link between two provenance nodes."""

    source: str
    target: str
    relation: str


@dataclass
class ProvenanceGraph:
    """A reconstructed causal graph over events."""

    nodes: dict[str, ProvenanceNode] = field(default_factory=dict)
    links: list[ProvenanceLink] = field(default_factory=list)

    def add_event(self, event: AgentEvent) -> None:
        self.nodes[event.event_id] = ProvenanceNode(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
            timestamp=event.timestamp.isoformat(),
        )

    def add_link(self, source: str, target: str, relation: str) -> None:
        self.links.append(ProvenanceLink(source, target, relation))

    def trail(self, event_id: str) -> list[str]:
        """Return the causal chain ending at ``event_id``.

        Uses the chronological ``follows`` links: find the earliest event in
        the chain (one with no incoming ``follows`` link) and walk forward to
        ``event_id``, producing the ordered cause-effect sequence.
        """
        by_source: dict[str, list[ProvenanceLink]] = {}
        by_target: dict[str, list[ProvenanceLink]] = {}
        for link in self.links:
            by_source.setdefault(link.source, []).append(link)
            by_target.setdefault(link.target, []).append(link)

        # find the first node in the chain
        start = event_id
        visited = set()
        while start in by_target:
            # move to the predecessor via the follows link
            pred = None
            for link in by_target.get(start, ()):
                if link.relation == "follows":
                    pred = link.source
                    break
            if pred is None or pred in visited:
                break
            visited.add(start)
            start = pred

        # walk forward from start to event_id
        chain: list[str] = []
        current: str | None = start
        chain_set: set[str] = set()
        while current is not None and current not in chain_set:
            chain.append(current)
            chain_set.add(current)
            if current == event_id:
                break
            for link in by_source.get(current, []):
                if link.relation == "follows":
                    current = link.target
                    break
            else:
                current = None
        return chain
class ProvenanceEngine:
    """Builds provenance graphs from a flight recorder's event stream.

    A ``follows`` edge connects each event to the next within the same
    execution, forming an ordered causal chain. Trajectories are therefore
    always chronological.
    """

    def __init__(self, recorder: AgentFlightRecorder) -> None:
        self._recorder = recorder

    def build(self, execution_id: str | None = None) -> ProvenanceGraph:
        graph = ProvenanceGraph()
        events = self._recorder.events(execution_id)
        grouped: dict[str, list[AgentEvent]] = {}
        for event in events:
            graph.add_event(event)
            key = str(event.execution_id) if event.execution_id else "_"
            grouped.setdefault(key, []).append(event)

        for chain in grouped.values():
            ordered = sorted(chain, key=lambda e: (e.timestamp, e.event_id))
            for prev, nxt in zip(ordered, ordered[1:], strict=False):
                graph.add_link(prev.event_id, nxt.event_id, "follows")
        return graph

    def explain(self, execution_id: str, last_event_id: str | None = None) -> list[dict]:
        """Return a JSON-ready causal explanation for an execution.

        The graph is built scoped to ``execution_id`` (the recorder filters
        the event stream), so the chronologically-last recorded node is the
        natural endpoint when ``last_event_id`` is omitted.
        """
        graph = self.build(execution_id)
        if last_event_id is None:
            if not graph.nodes:
                return []
            # chronological endpoint: latest recorded timestamp wins
            last_event_id = max(
                graph.nodes,
                key=lambda eid: graph.nodes[eid].timestamp,
            )
        return [
            {
                "event_id": node.event_id,
                "type": node.event_type,
                "payload": node.payload,
            }
            for node_id in graph.trail(last_event_id)
            if (node := graph.nodes.get(node_id)) is not None
        ]
