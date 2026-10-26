"""Replay engine: reconstructs execution history from recorded events.

Replay reconstructs trajectories and state transitions from the flight
recorder. It clearly distinguishes:

- *recorded* state (what events actually happened), and
- *reconstructed* state (the belief-state snapshot derived from those events).

Replay never re-executes tools; it is a read-only reconstruction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura_agent.flight_recorder.agent_flight_recorder import AgentFlightRecorder
from aura_agent.flight_recorder.events.agent_event import AgentEvent

__all__ = ["ReplayedEvent", "ReplayedTrajectory", "ReplayEngine"]


@dataclass(frozen=True)
class ReplayedEvent:
    """A single replayed step."""

    event: AgentEvent
    position: int


@dataclass
class ReplayedTrajectory:
    """The reconstructed trajectory for one execution."""

    execution_id: str
    steps: list[ReplayedEvent] = field(default_factory=list)
    reconstructed_state: dict = field(default_factory=dict)

    @property
    def event_types(self) -> list[str]:
        return [step.event.event_type for step in self.steps]

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "recorded_events": [
                {
                    "position": step.position,
                    "event_id": step.event.event_id,
                    "type": step.event.event_type,
                    "timestamp": step.event.timestamp.isoformat(),
                    "payload": step.event.payload,
                }
                for step in self.steps
            ],
            "reconstructed_state": self.reconstructed_state,
        }


class ReplayEngine:
    """Read-only trajectory reconstruction."""

    def __init__(self, recorder: AgentFlightRecorder) -> None:
        self._recorder = recorder

    def replay(self, execution_id: str) -> ReplayedTrajectory:
        events = self._recorder.events(execution_id)
        ordered = sorted(events, key=lambda e: (e.timestamp, e.event_id))
        steps = [ReplayedEvent(event=e, position=i) for i, e in enumerate(ordered)]

        # deterministic belief-state reconstruction: merge state-bearing
        # payload slices in chronological order
        reconstructed: dict = {}
        for step in steps:
            payload = step.event.payload
            if payload.get("observed_state") is not None:
                reconstructed.update(payload["observed_state"])
            if payload.get("result_state") is not None:
                reconstructed.update(payload["result_state"])
        return ReplayedTrajectory(
            execution_id=execution_id,
            steps=steps,
            reconstructed_state=reconstructed,
        )

    def event_inspection(self, execution_id: str, event_type: str) -> list[AgentEvent]:
        return [
            e
            for e in self._recorder.events(execution_id)
            if e.event_type == event_type
        ]
