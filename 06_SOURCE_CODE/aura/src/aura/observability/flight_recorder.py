"""Intelligence flight recorder.

An append-only trajectory of everything that matters: goals, observations,
decisions, plans, actions, permission/safety outcomes, tool executions,
validations, evaluations, recoveries, and reflections. Every event carries an
id, execution id, correlation id, timestamp, source, event type, sequence, and
payload.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import CorrelationId, EventId, ExecutionId
from aura.foundation.serialization import to_jsonable


@dataclass(frozen=True, slots=True)
class EventRecord:
    event_id: EventId
    execution_id: ExecutionId
    correlation_id: CorrelationId
    timestamp: str
    source: str
    event_type: str
    sequence: int
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "execution_id": str(self.execution_id),
            "correlation_id": str(self.correlation_id),
            "timestamp": self.timestamp,
            "source": self.source,
            "event_type": self.event_type,
            "sequence": self.sequence,
            "payload": to_jsonable(self.payload),
        }


class FlightRecorder:
    """Append-only recorder. Overrides decide where events are stored."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._sequence = 0
        self._lock = threading.RLock()

    def record(
        self,
        *,
        event_type: str,
        source: str,
        execution_id: ExecutionId,
        correlation_id: CorrelationId,
        payload: dict[str, Any] | None = None,
    ) -> EventRecord:
        with self._lock:
            self._sequence += 1
            event = EventRecord(
                event_id=EventId.new(),
                execution_id=execution_id,
                correlation_id=correlation_id,
                timestamp=self._clock.utcnow_iso(),
                source=source,
                event_type=event_type,
                sequence=self._sequence,
                payload=payload or {},
            )
            self._append(event)
            return event

    def _append(self, event: EventRecord) -> None:
        raise NotImplementedError

    def events(self, **filters: Any) -> list[EventRecord]:
        raise NotImplementedError

    def count(self) -> int:
        return len(self.events())


class InMemoryFlightRecorder(FlightRecorder):
    """Flight recorder holding events in memory (default, deterministic)."""

    def __init__(self, clock: Clock | None = None) -> None:
        super().__init__(clock=clock)
        self._store: list[EventRecord] = []

    def _append(self, event: EventRecord) -> None:
        self._store.append(event)

    def events(self, **filters: Any) -> list[EventRecord]:
        result: list[EventRecord] = list(self._store)
        for key, value in filters.items():
            if value is None:
                continue
            result = [e for e in result if getattr(e, key) == value]
        return result


class FileFlightRecorder(FlightRecorder):
    """Append-only JSON-lines flight recorder. Durable across restarts."""

    def __init__(self, path: str | Path, clock: Clock | None = None) -> None:
        super().__init__(clock=clock)
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self._path.open("a", encoding="utf-8")

    def _append(self, event: EventRecord) -> None:
        self._handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._handle.flush()

    def events(self, **filters: Any) -> list[EventRecord]:
        self._handle.flush()
        with self._path.open("r", encoding="utf-8") as source:
            lines = [json.loads(line) for line in source if line.strip()]
        records: list[EventRecord] = []
        for raw in lines:
            records.append(
                EventRecord(
                    event_id=EventId.from_str(raw["event_id"]),
                    execution_id=ExecutionId.from_str(raw["execution_id"]),
                    correlation_id=CorrelationId.from_str(raw["correlation_id"]),
                    timestamp=raw["timestamp"],
                    source=raw["source"],
                    event_type=raw["event_type"],
                    sequence=raw["sequence"],
                    payload=raw["payload"],
                )
            )
        for key, value in filters.items():
            if value is None:
                continue
            records = [e for e in records if getattr(e, key) == value]
        return records

    def close(self) -> None:
        self._handle.close()


__all__ = ["EventRecord", "FileFlightRecorder", "FlightRecorder", "InMemoryFlightRecorder"]