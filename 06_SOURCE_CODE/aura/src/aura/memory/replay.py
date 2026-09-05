"""Replay to memory.

Extracts execution episodes from the flight recorder into episodic memory so
past executions are retrievable for debugging, learning, and reflection.
"""

from __future__ import annotations

from aura.foundation.clock import Clock
from aura.foundation.ids import ExecutionId
from aura.memory.models import MemoryEntry, MemoryType, Provenance
from aura.memory.store import MemoryStore
from aura.observability.flight_recorder import FlightRecorder

_EPISODE_TYPES = {
    "goal.created",
    "decision",
    "action.executed",
    "observation.recorded",
    "reflection.completed",
}


class ReplayToMemory:
    def __init__(self, store: MemoryStore, clock: Clock | None = None) -> None:
        self._store = store
        self._clock = clock

    def ingest_execution(
        self, recorder: FlightRecorder, execution_id: ExecutionId
    ) -> list[MemoryEntry]:
        events = [
            e
            for e in recorder.events(execution_id=execution_id)
            if e.event_type in _EPISODE_TYPES
        ]
        entries: list[MemoryEntry] = []
        for event in sorted(events, key=lambda e: e.sequence):
            entry = MemoryEntry.create(
                key=f"episode:{event.event_type}",
                kind=MemoryType.EPISODIC,
                content={**event.payload, "event_id": str(event.event_id)},
                importance=0.6,
                provenance=Provenance(
                    source="flight_recorder", execution_id=execution_id, creator="replay"
                ),
                clock=self._clock,
            )
            self._store.add(entry)
            entries.append(entry)
        return entries


__all__ = ["ReplayToMemory"]