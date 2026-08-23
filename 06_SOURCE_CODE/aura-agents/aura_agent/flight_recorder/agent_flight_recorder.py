"""Agent flight recorder: records the complete execution trajectory.

Every meaningful runtime event (goal received, decision, plan created,
capability verified, permission granted, safety approved, tool invoked,
result validated, etc.) is appended to the event store with correlation data.
"""

from __future__ import annotations

from aura_agent.flight_recorder.events.agent_event import AgentEvent
from aura_agent.flight_recorder.storage.event_store import (
    EventStore,
    InMemoryEventStore,
)

__all__ = ["AgentFlightRecorder"]


class AgentFlightRecorder:
    """Append-only trajectory recorder backed by an ``EventStore``."""

    def __init__(self, store: EventStore | None = None) -> None:
        self._store = store or InMemoryEventStore()

    @property
    def store(self) -> EventStore:
        return self._store

    def record(self, event: AgentEvent) -> None:
        """Append an event to the trajectory."""
        self._store.append(event)

    def events(self, execution_id: str | None = None) -> list[AgentEvent]:
        """Return events, optionally filtered by execution id."""
        return self._store.query(execution_id=execution_id)

    def event_types(self) -> list[str]:
        return [e.event_type for e in self._store.query()]

    def trajectory(self, execution_id: str) -> list[dict]:
        """Human-readable trajectory for one execution."""
        out: list[dict] = []
        for event in self._store.query(execution_id=execution_id):
            out.append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type,
                    "payload": event.payload,
                }
            )
        return out

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store) if hasattr(self._store, "__len__") else 0