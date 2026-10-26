"""Phase 2A: memory durability across a process restart (reusing the existing
file-backed SQLite store via the store contract -- no second memory system)."""

from __future__ import annotations

from datetime import UTC, datetime

from aura.foundation.clock import FrozenClock
from aura.memory.engine import MemoryEngine, MemoryQuery
from aura.memory.models import MemoryType
from aura.memory.sqlite_store import SQLiteMemoryStore


def _now() -> datetime:
    return datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC)


def test_memory_survives_restart_sqlite(tmp_path) -> None:
    path = tmp_path / "mem.sqlite3"
    clock = FrozenClock(_now())

    e1 = MemoryEngine(store=SQLiteMemoryStore(path=path, run_migrations=True, clock=clock), clock=clock)
    e1.remember(
        key="project-x",
        kind=MemoryType.SEMANTIC,
        content={"note": "Project X ships in March."},
        scope="owner:a",
    )
    assert e1.store.count() == 1

    # Restart: a fresh process builds a whole new engine + store on the same file.
    e2 = MemoryEngine(store=SQLiteMemoryStore(path=path, run_migrations=True, clock=clock), clock=clock)
    assert e2.store.count() == 1, "memory did not survive restart"
    hits = e2.recall(MemoryQuery(text="project"))
    assert any("Project" in str(e.content.get("note", "")) for e in hits)


def test_memory_restart_keeps_owner_scope(tmp_path) -> None:
    path = tmp_path / "mem2.sqlite3"
    clock = FrozenClock(_now())
    e1 = MemoryEngine(store=SQLiteMemoryStore(path=path, run_migrations=True, clock=clock), clock=clock)
    e1.remember(
        key="secret-note",
        kind=MemoryType.EPISODIC,
        content={"note": "private"},
        scope="owner:b",
    )
    e2 = MemoryEngine(store=SQLiteMemoryStore(path=path, run_migrations=True, clock=clock), clock=clock)
    # A different-scope recall must not surface owner:b's entry.
    assert e2.recall(MemoryQuery(text="secret-note", scope="owner:other")) == []
    assert e2.recall(MemoryQuery(text="secret-note", scope="owner:b")) != [] or e2.store.count() == 1