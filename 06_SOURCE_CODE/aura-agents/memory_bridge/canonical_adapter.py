"""Canonical AURA memory provider adapter.

Bridges the agent runtime to the canonical AURA memory engine through the
``MemoryProvider`` protocol. This is the sanctioned integration path: the agent
never re-implements memory semantics — it delegates every read/write to
``aura.memory.MemoryEngine``.

The import is lazy so ``aura-agent`` remains importable when the canonical
runtime is not installed; the adapter only becomes usable when both packages
are present.
"""

from __future__ import annotations

from typing import Any

from aura_agent.memory_bridge.models import MemoryEntry, MemoryQuery, MemoryRecord

__all__ = ["CanonicalMemoryProvider"]

# Agent-kind -> canonical MemoryType mapping. Experience/outcome/reflection
# records are episodic by nature; purely factual agent knowledge maps to
# semantic memory.
_KIND_MAP = {
    "experience": "episodic",
    "outcome": "episodic",
    "reflection": "episodic",
    "semantic": "semantic",
    "episodic": "episodic",
}


class CanonicalMemoryProvider:
    """Adapts the canonical AURA memory engine to the agent MemoryProvider."""

    def __init__(self, engine: Any) -> None:
        from aura.memory.models import MemoryType  # noqa: F401  (validate availability)

        self._engine = engine

    @property
    def engine(self) -> Any:
        return self._engine

    # -- protocol: write ------------------------------------------------------
    def write(self, entry: MemoryEntry) -> None:
        from aura.memory.models import MemoryType, Provenance
        from aura.memory.engine import MemoryQuery as _  # noqa: F401

        kind = _KIND_MAP.get(entry.kind, entry.kind)
        try:
            canonical_kind = MemoryType(kind)
        except ValueError:
            canonical_kind = MemoryType.EPISODIC
        self._engine.remember(
            key=entry.key,
            kind=canonical_kind,
            content=_content(entry.content),
            provenance=Provenance(source="agent.memory_bridge", creator=entry.correlation_id or "agent"),
        )

    # -- protocol: retrieve ----------------------------------------------------
    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        from aura.memory.engine import MemoryQuery as CanonicalQuery

        canonical = self._engine.recall(
            CanonicalQuery(text=query.key or "", limit=query.limit)
        )
        records: list[MemoryRecord] = []
        for found in canonical:
            if query.kind != "*" and found.kind.value != _KIND_MAP.get(query.kind, query.kind):
                continue
            records.append(
                MemoryRecord(
                    entry=MemoryEntry(
                        key=found.key,
                        kind=found.kind.value,
                        content=found.content,
                        metadata={"importance": found.importance, "id": str(found.id)},
                        correlation_id=found.provenance.creator,
                    ),
                    score=round(found.confidence.combined, 6),
                )
            )
        return records


def _content(value: Any) -> dict[str, Any]:
    """Normalize arbitrary content into the dict shape canonical memory uses."""
    import dataclasses

    if isinstance(value, dict):
        return value
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return {"value": value}