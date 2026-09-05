"""Memory domain tests: working/episodic/semantic/procedural, confidence, provenance, linking, forgetting."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aura.foundation.clock import ManualClock
from aura.foundation.errors import NotFoundError
from aura.memory.engine import MemoryEngine, MemoryQuery
from aura.memory.models import (
    LinkKind,
    MemoryConfidence,
    MemoryType,
    Provenance,
)


def make_engine() -> MemoryEngine:
    return MemoryEngine(clock=ManualClock(0))


def test_remember_and_get() -> None:
    engine = make_engine()
    entry = engine.remember(key="alpha", kind=MemoryType.EPISODIC, content={"value": 1})
    assert engine.get(entry.id).content == {"value": 1}
    assert engine.store.count() == 1


def test_memory_type_kinds() -> None:
    engine = make_engine()
    for kind in MemoryType:
        entry = engine.remember(key=kind.value, kind=kind, content={"k": kind.value})
        assert entry.kind is kind


def test_recall_ranking() -> None:
    engine = make_engine()
    engine.remember(key="match", kind=MemoryType.SEMANTIC, content={"text": "the purple sky at dawn"}, importance=0.9)
    engine.remember(key="other", kind=MemoryType.SEMANTIC, content={"text": "unrelated content"}, importance=0.1)
    found = engine.recall(MemoryQuery(text="purple sky"))
    assert found
    assert found[0].key == "match"


def test_recall_limit() -> None:
    engine = make_engine()
    for i in range(5):
        engine.remember(key=f"k{i}", kind=MemoryType.WORKING, content={"i": i})
    assert len(engine.recall(MemoryQuery(limit=2))) == 2


def test_forget() -> None:
    engine = make_engine()
    entry = engine.remember(key="temp", kind=MemoryType.WORKING, content={})
    engine.forget(entry.id)
    with pytest.raises(NotFoundError):
        engine.get(entry.id)


def test_link_entries() -> None:
    engine = make_engine()
    a = engine.remember(key="a", kind=MemoryType.EPISODIC, content={})
    b = engine.remember(key="b", kind=MemoryType.EPISODIC, content={})
    engine.link(a.id, b.id, LinkKind.CAUSAL)
    assert str(b.id) in a.links
    assert a.links[str(b.id)] is LinkKind.CAUSAL


def test_memory_confidence_multiaxis() -> None:
    confidence = MemoryConfidence(fact=0.9, source=0.8, freshness=0.7, relevance=0.6)
    assert 0.0 <= confidence.combined <= 1.0
    with pytest.raises(ValueError):
        MemoryConfidence(fact=1.5)


def test_provenance_tracking() -> None:
    engine = make_engine()
    provenance = Provenance(source="reasoning.engine", creator="test")
    entry = engine.remember(key="proven", kind=MemoryType.SEMANTIC, content={}, provenance=provenance)
    assert entry.provenance.source == "reasoning.engine"


def test_consolidation() -> None:
    engine = make_engine()
    engine.remember(key="x", kind=MemoryType.EPISODIC, content={"summary": "old"}, importance=0.9)
    summaries = engine.consolidate()
    for summary in summaries:
        assert summary.kind is MemoryType.SEMANTIC


def test_forgetting_policy() -> None:
    clock = ManualClock(0)
    engine = MemoryEngine(clock=clock)
    entry = engine.remember(
        key="expiring",
        kind=MemoryType.WORKING,
        content={},
        expires_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    clock.advance(3600 * 24 * 400)  # past 2026 expiry
    removed = engine.enforce_forgetting()
    assert entry.id in removed
    assert engine.store.count() == 0


def test_memory_is_not_global() -> None:
    engine_a = make_engine()
    engine_b = make_engine()
    engine_a.remember(key="private", kind=MemoryType.WORKING, content={"secret": True})
    assert engine_a.store.count() == 1
    assert engine_b.store.count() == 0