"""Memory bridge: provider protocol, in-memory store, and writing helpers.

Integration contract with AURA Memory:
- retrieval: episodic, semantic, and experience queries
- writing: experiences, outcomes, and reflection records

A provider is injected; there are no hidden globals. The in-memory
implementation exists so tests and local operation never need a memory server.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aura_agent.memory_bridge.models import (
    Experience,
    MemoryEntry,
    MemoryQuery,
    MemoryRecord,
)

__all__ = ["MemoryProvider", "InMemoryMemory", "MemoryBridge"]


@runtime_checkable
class MemoryProvider(Protocol):
    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]: ...
    def write(self, entry: MemoryEntry) -> None: ...


class InMemoryMemory:
    """Dependency-free in-memory memory store for tests and local use."""

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        hits: list[MemoryRecord] = []
        for entry in self._entries:
            if query.kind != "*" and entry.kind != query.kind:
                continue
            if query.key is not None and entry.key != query.key:
                continue
            score = _simple_relevance(query, entry)
            hits.append(MemoryRecord(entry=entry, score=score))
            if len(hits) >= query.limit:
                break
        return hits

    def write(self, entry: MemoryEntry) -> None:
        self._entries = [entry] + self._entries
        if len(self._entries) > 1000:  # bounded
            self._entries = self._entries[:1000]

    def __len__(self) -> int:
        return len(self._entries)


def _simple_relevance(query: MemoryQuery, entry: MemoryEntry) -> float:
    """Deterministic relevance: key match scores 1.0, kind match 0.5."""
    score = 0.0
    if query.key and entry.key == query.key:
        score += 1.0
    if query.kind != "*" and entry.kind == query.kind:
        score += 0.5
    return score
class MemoryBridge:
    """Composes episodic/semantic/experience retrieval and writing.

    This is the *only* surface the agent runtime uses to talk to memory; it
    delegates to an injected ``MemoryProvider`` with zero state of its own.
    """

    def __init__(self, provider: MemoryProvider | None = None) -> None:
        self._provider = provider or InMemoryMemory()

    @property
    def provider(self) -> MemoryProvider:
        return self._provider

    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        return self._provider.retrieve(query)

    def write(self, entry: MemoryEntry) -> None:
        self._provider.write(entry)

    # convenience writers -------------------------------------------------
    def write_experience(
        self, experience: Experience, *, correlation_id: str | None = None
    ) -> None:
        self.write(
            MemoryEntry(
                key=f"exp:{experience.action}",
                kind="experience",
                content=experience,
                metadata={
                    "succeeded": experience.succeeded,
                    "note": experience.note,
                },
                correlation_id=correlation_id,
            )
        )

    def write_outcome(
        self,
        *,
        actor: str,
        action: str,
        succeeded: bool,
        correlation_id: str | None = None,
    ) -> None:
        self.write(
            MemoryEntry(
                key=f"out:{action}:{actor}",
                kind="outcome",
                content={"succeeded": succeeded},
                correlation_id=correlation_id,
            )
        )

    def write_reflection(
        self, *, text: str, correlation_id: str | None = None
    ) -> None:
        self.write(
            MemoryEntry(
                key=f"ref:{correlation_id or 'session'}",
                kind="reflection",
                content=text,
                correlation_id=correlation_id,
            )
        )