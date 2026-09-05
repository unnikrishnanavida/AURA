"""Memory policy and lifecycle tests: sensitivity clearance, versioned correction, retention purge, lineage pruning."""

from __future__ import annotations

import pytest

from aura.foundation.clock import ManualClock
from aura.foundation.errors import NotFoundError
from aura.memory.engine import MemoryEngine
from aura.memory.models import (
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from aura.memory.policy import MemoryLifecycle, MemoryPolicy

# Internal records require clearance >= 1; tests hold full clearance unless a
# test explicitly verifies the access gate.
FULL_CLEARANCE = 3


def make_engine() -> MemoryEngine:
    return MemoryEngine(clock=ManualClock(0))


def make_entry(engine: MemoryEngine, *, sensitivity: Sensitivity = Sensitivity.INTERNAL) -> MemoryEntry:
    return engine.remember(
        key="secret-note",
        kind=MemoryType.EPISODIC,
        content={"text": "original"},
        sensitivity=sensitivity,
    )


def test_policy_denies_below_required_clearance() -> None:
    policy = MemoryPolicy()
    decision = policy.can_access(Sensitivity.RESTRICTED, clearance=0)
    assert not decision.allowed
    assert decision.required_clearance == 3


def test_policy_allows_sufficient_clearance() -> None:
    policy = MemoryPolicy()
    assert policy.can_access(Sensitivity.RESTRICTED, clearance=3).allowed
    assert policy.can_access(Sensitivity.PUBLIC, clearance=0).allowed


def test_policy_deny_by_default() -> None:
    policy = MemoryPolicy()
    # RESTRICTED is rank 3; anonymous (None) holds 0
    decision = policy.can_access(Sensitivity.RESTRICTED, clearance=None)
    assert not decision.allowed


def test_policy_require_raises() -> None:
    policy = MemoryPolicy()
    with pytest.raises(PermissionError):
        policy.require(Sensitivity.SENSITIVE, clearance=1)


def test_versioned_correction_keeps_history() -> None:
    engine = make_engine()
    entry = make_entry(engine)
    lifecycle = MemoryLifecycle(engine=engine, clock=engine._clock)
    correction = lifecycle.correct(
        entry.id,
        content={"text": "corrected"},
        provenance=Provenance(source="human.review", creator="test"),
        clearance=FULL_CLEARANCE,
    )
    current = correction.current
    assert current.version == 2
    assert current.supersedes == entry.id
    # predecessor kept for provenance, marked superseded
    assert engine.by_id(entry.id).status is MemoryStatus.SUPERSEDED


def test_correction_requires_clearance_for_sensitive() -> None:
    engine = make_engine()
    entry = make_entry(engine, sensitivity=Sensitivity.SENSITIVE)
    lifecycle = MemoryLifecycle(engine=engine)
    with pytest.raises(PermissionError):
        lifecycle.correct(
            entry.id,
            content={"text": "nope"},
            provenance=Provenance(source="x"),
            clearance=0,
        )
    # original untouched when access was denied
    assert engine.by_id(entry.id).content == {"text": "original"}


def test_retention_ttl_purge() -> None:
    engine = make_engine()
    lifecycle = MemoryLifecycle(engine=engine, clock=engine._clock)
    engine.remember(
        key="volatile",
        kind=MemoryType.WORKING,
        content={},
        retention=RetentionPolicy(ttl_seconds=100),
    )
    engine._clock.advance(101)
    removed = lifecycle.purge_expired(engine._clock.now())
    assert len(removed) == 1
    assert engine.store.count() == 0


def test_lineage_pruning_removes_oldest() -> None:
    engine = make_engine()
    lifecycle = MemoryLifecycle(engine=engine, clock=engine._clock)
    first = make_entry(engine)
    second = lifecycle.correct(
        first.id,
        content={"text": "v2"},
        provenance=Provenance(source="a"),
        clearance=FULL_CLEARANCE,
    ).current
    third = lifecycle.correct(
        second.id,
        content={"text": "v3"},
        provenance=Provenance(source="b"),
        clearance=FULL_CLEARANCE,
    ).current
    # max_versions=2 -> keep the two newest (second+third), purge first
    pruned = lifecycle.prune_lineage(third, retention=RetentionPolicy(max_versions=2))
    assert first.id in pruned
    assert second.id not in pruned
    with pytest.raises(NotFoundError):
        engine.by_id(first.id)
    assert engine.store.count() == 2


def test_retention_policy_validation() -> None:
    with pytest.raises(ValueError):
        RetentionPolicy(ttl_seconds=0)
    with pytest.raises(ValueError):
        RetentionPolicy(max_versions=0)