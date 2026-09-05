"""Memory engine.

The composed public memory API: remember, recall, forget, link, consolidate,
and replay ingestion. Uses injected store/clock/graph so memory is never a
hidden global.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.ids import ExecutionId, MemoryId
from aura.memory.consolidation import Consolidator, ForgettingPolicy
from aura.memory.graph import MemoryGraph
from aura.memory.models import (
    LinkKind,
    MemoryConfidence,
    MemoryEntry,
    MemoryType,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from aura.memory.retrieval import RetrievalScorer
from aura.memory.store import InMemoryMemoryStore, MemoryStore


@dataclass
class MemoryQuery:
    text: str = ""
    kind: MemoryType | None = None
    tags: tuple[str, ...] = ()
    limit: int = 10


class FlightRecorderLike(Protocol):
    def events(self, **filters: Any) -> list[Any]: ...


class MemoryEngine:
    def __init__(
        self,
        *,
        store: MemoryStore | None = None,
        graph: MemoryGraph | None = None,
        clock: Clock | None = None,
        scorer: RetrievalScorer | None = None,
        consolidator: Consolidator | None = None,
        forgetting: ForgettingPolicy | None = None,
    ) -> None:
        self.store = store or InMemoryMemoryStore()
        self.graph = graph or MemoryGraph()
        self._clock = clock or SystemClock()
        self._scorer = scorer or RetrievalScorer()
        self._consolidator = consolidator or Consolidator()
        self._forgetting = forgetting or ForgettingPolicy()

    # -- write -------------------------------------------------------------
    def remember(
        self,
        *,
        key: str,
        kind: MemoryType,
        content: dict[str, Any],
        importance: float = 0.5,
        confidence: MemoryConfidence | None = None,
        provenance: Provenance | None = None,
        tags: tuple[str, ...] = (),
        expires_at: datetime | None = None,
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        observed_at: datetime | None = None,
        retention: RetentionPolicy | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry.create(
            key=key,
            kind=kind,
            content=content,
            importance=importance,
            confidence=confidence,
            provenance=provenance,
            clock=self._clock,
            expires_at=expires_at,
            tags=tags,
            sensitivity=sensitivity,
            observed_at=observed_at,
            retention=retention,
        )
        self.store.add(entry)
        self.graph.register(entry)
        return entry

    def get(self, memory_id: MemoryId) -> MemoryEntry:
        entry = self.store.get(memory_id)
        entry.touch(self._clock)
        return entry

    def forget(self, memory_id: MemoryId) -> None:
        self.store.delete(memory_id)

    def link(self, source: MemoryId, target: MemoryId, kind: LinkKind) -> None:
        from_entry = self.store.get(source)
        to_entry = self.store.get(target)
        from_entry.links[str(target)] = kind
        to_entry.links[str(source)] = kind
        self.graph.link(from_entry, to_entry, kind)

    # -- read ---------------------------------------------------------------
    def recall(self, query: MemoryQuery) -> list[MemoryEntry]:
        candidates = self.store.search(text=query.text, kind=query.kind, tags=query.tags)
        ranked = sorted(
            candidates,
            key=lambda e: self._scorer.score(e, query.text, now=self._clock.now()),
            reverse=True,
        )
        for entry in ranked[: query.limit]:
            entry.touch(self._clock)
        return ranked[: query.limit]

    def by_id(self, memory_id: MemoryId) -> MemoryEntry:
        return self.store.get(memory_id)

    def recent(self, *, kind: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        entries = [e for e in self.store.all() if kind is None or e.kind is kind]
        entries.sort(key=lambda e: e.last_access, reverse=True)
        return entries[:limit]

    # -- maintenance ----------------------------------------------------------
    def consolidate(self) -> list[MemoryEntry]:
        summaries = self._consolidator.consolidate(list(self.store.all()))
        for summary in summaries:
            self.store.add(summary)
            self.graph.register(summary)
        return summaries

    def enforce_forgetting(self) -> list[MemoryId]:
        removed: list[MemoryId] = []
        for entry in list(self.store.all()):
            if self._forgetting.eligible(entry, self._clock.now()):
                removed.append(entry.id)
                self.store.delete(entry.id)
        return removed

    def ingest_execution(self, recorder: FlightRecorderLike, execution_id: ExecutionId) -> list[MemoryEntry]:
        from aura.memory.replay import ReplayToMemory

        return ReplayToMemory(self.store, clock=self._clock).ingest_execution(recorder, execution_id)  # type: ignore[arg-type]

    def health(self) -> dict[str, object]:
        return {"status": "ok", "entries": self.store.count()}


__all__ = ["MemoryEngine", "MemoryQuery"]