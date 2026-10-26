"""Phase 2A: learning registry durability across a restart.

Proves the 2A.5 gate: versioned learned behaviour (and its rollback state)
survives a process restart, and a previously rolled-back change is never
reactivated by a restart.
"""

from __future__ import annotations

from aura.learning.models import LearningSignal
from aura.learning.registry import LearningRegistry


def test_rollback_state_survives_restart(tmp_path) -> None:
    path = str(tmp_path / "learn.sqlite3")

    signal = LearningSignal.create(kind="lesson", content="use vectorized ops")
    reg1 = LearningRegistry(state_path=path)
    change = reg1.apply(signal)
    assert reg1.active() != []
    reg1.rollback(change.ref)  # operator rolls the applied change back
    assert reg1.active() == []

    # Restart: rolled-back behaviour must remain inactive, never reactivated.
    reg2 = LearningRegistry(state_path=path)
    assert reg2.active() == [], "rolled-back learning was reactivated by restart"
    hist = reg2.history()
    assert len(hist) == 1 and hist[0].ref == change.ref
    assert hist[0].rolled_back_at is not None


def test_active_learning_survives_restart(tmp_path) -> None:
    path = str(tmp_path / "learn2.sqlite3")
    signal = LearningSignal.create(kind="improvement", content="cache frequent queries")
    reg1 = LearningRegistry(state_path=path)
    change = reg1.apply(signal)
    assert reg1.active() != []

    reg2 = LearningRegistry(state_path=path)
    assert [c.ref for c in reg2.active()] == [change.ref]
    # lineage preserved too
    assert reg2.lineage_of(signal.id) == []


def test_empty_registry_starts_clean(tmp_path) -> None:
    reg = LearningRegistry(state_path=str(tmp_path / "learn3.sqlite3"))
    assert reg.active() == []
    assert reg.history() == []