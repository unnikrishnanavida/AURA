"""Event store abstraction for the flight recorder.

The event store is a persistence boundary. This file defines the protocol and
an in-memory implementation; a SQLite or PostgreSQL implementation can be
added later without touching recorder callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from aura_agent.flight_recorder.events.agent_event import AgentEvent

__all__ = ["EventStore", "InMemoryEventStore", "SQLiteEventStore"]


class EventStore(Protocol):
    """Backend for recording and reading agent events."""

    def append(self, event: AgentEvent) -> None: ...
    def query(self, *, execution_id: str | None = None) -> list[AgentEvent]: ...
    def clear(self) -> None: ...


@dataclass
class InMemoryEventStore:
    """Append-only in-memory event store (default backend)."""

    _events: list[AgentEvent] = field(default_factory=list)

    def append(self, event: AgentEvent) -> None:
        self._events.append(event)

    def query(self, *, execution_id: str | None = None) -> list[AgentEvent]:
        if execution_id is None:
            return list(self._events)
        return [
            e for e in self._events if (e.execution_id is not None and str(e.execution_id)) == execution_id
        ]

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)


class SQLiteEventStore:
    """SQLite-backed event store.

    INTERFACE READY -- implementation pending an explicit storage decision in
    the AURA ecosystem. Kept as a named class so imports across the runtime
    remain stable.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path or ":memory:"

    def append(self, event: AgentEvent) -> None:  # pragma: no cover - pending
        raise NotImplementedError("SQLiteEventStore: IMPLEMENTATION PENDING")

    def query(self, *, execution_id: str | None = None) -> list[AgentEvent]:  # pragma: no cover - pending
        raise NotImplementedError("SQLiteEventStore: IMPLEMENTATION PENDING")

    def clear(self) -> None:  # pragma: no cover - pending
        raise NotImplementedError("SQLiteEventStore: IMPLEMENTATION PENDING")