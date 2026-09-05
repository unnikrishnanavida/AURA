"""Replay.

Replay reconstructs what happened from recorded trajectories. It never claims
deterministic reconstruction where external dependencies were
nondeterministic: every reconstructed state is explicitly flagged
``RECONSTRUCTED`` and every recorded snapshot ``RECORDED``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.errors import NotFoundError
from aura.foundation.ids import ExecutionId
from aura.observability.flight_recorder import EventRecord, FlightRecorder
from aura.observability.provenance import ProvenanceGraph

STATE_MARKER = "state_snapshot"


@dataclass(frozen=True)
class StateReconstruction:
    at_sequence: int
    state: dict[str, Any]
    origin: str  # RECORDED | RECONSTRUCTED


@dataclass
class ReplayResult:
    execution_id: ExecutionId
    events: list[EventRecord] = field(default_factory=list)
    states: list[StateReconstruction] = field(default_factory=list)

    def trajectory(self) -> list[EventRecord]:
        return sorted(self.events, key=lambda e: e.sequence)

    @property
    def reconstructable(self) -> bool:
        return len(self.events) > 0


class ReplayEngine:
    """Read-only reconstruction of executions from flight-recorder events."""

    def __init__(self, recorder: FlightRecorder) -> None:
        self._recorder = recorder

    def trajectory(self, execution_id: ExecutionId) -> ReplayResult:
        events = self._recorder.events(execution_id=execution_id)
        if not events and not self._recorder.events():
            raise NotFoundError(f"no recorded execution: {execution_id}")
        states: list[StateReconstruction] = []
        for event in sorted(events, key=lambda e: e.sequence):
            if event.event_type == STATE_MARKER:
                states.append(
                    StateReconstruction(
                        at_sequence=event.sequence,
                        state=dict(event.payload.get("state", {})),
                        origin=event.payload.get("origin", "RECORDED"),
                    )
                )
        return ReplayResult(execution_id=execution_id, events=events, states=states)

    def state_at(self, execution_id: ExecutionId, sequence: int) -> StateReconstruction | None:
        replay = self.trajectory(execution_id)
        applicable = [s for s in replay.states if s.at_sequence <= sequence]
        return applicable[-1] if applicable else None

    def graph(self, execution_id: ExecutionId) -> ProvenanceGraph:
        graph = ProvenanceGraph()
        graph.load(self.trajectory(execution_id).events)
        return graph


__all__ = ["ReplayEngine", "ReplayResult", "StateReconstruction"]