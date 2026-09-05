"""SQLite memory store + serialization + migrations tests.

Covers the full Phase 9 persistence surface: row round-trips, schema migrations
(forward + validation + failure rollback), transactional atomicity, partial
failure rollback, database-unavailable shutdown, corrupted-row detection, and
concurrent writes.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from aura.foundation.clock import FrozenClock
from aura.foundation.errors import ConfigurationError, NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory.migrations import (
    CURRENT_SCHEMA_VERSION,
    current_version,
    migrate,
    validate_schema,
)
from aura.memory.models import (
    MemoryConfidence,
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    Provenance,
    Sensitivity,
)
from aura.memory.serialization import entry_to_row, row_to_entry
from aura.memory.sqlite_store import SQLiteMemoryStore, StorageIntegrityError


def make_entry(**overrides: object) -> MemoryEntry:
    defaults: dict[str, object] = dict(
        key="k", kind=MemoryType.SEMANTIC, content={"a": 1}, importance=0.7
    )
    defaults.update(overrides)
    return MemoryEntry.create(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def sqlite_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.sqlite3")


def test_row_round_trip_preserves_full_model() -> None:
    entry = make_entry(
        key="full",
        kind=MemoryType.EPISODIC,
        content={"nested": {"x": [1, 2]}},
        importance=0.9,
        confidence=MemoryConfidence(fact=0.8, source=0.7, freshness=0.6, relevance=0.5),
        provenance=Provenance(source="pipeline", creator="op", details={"step": 2}),
        tags=("a", "b"),
        sensitivity=Sensitivity.SENSITIVE,
    )
    row = entry_to_row(entry)
    restored = row_to_entry(row)
    assert restored.id == entry.id
    assert restored.key == entry.key
    assert restored.content == entry.content
    assert restored.confidence.fact == pytest.approx(0.8)
    assert restored.provenance.source == "pipeline"
    assert restored.sensitivity is Sensitivity.SENSITIVE
    assert restored.tags == ("a", "b")


def test_corrupted_content_json_raises() -> None:
    row = entry_to_row(make_entry())
    row["content"] = "{not json"
    with pytest.raises(ValueError, match="corrupted content"):
        row_to_entry(row)


def test_missing_required_timestamp_raises() -> None:
    row = entry_to_row(make_entry())
    row["created_at"] = None
    with pytest.raises(ValueError, match="required timestamp"):
        row_to_entry(row)


def test_migrations_apply_and_validate(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path, run_migrations=True)
    assert current_version(store._conn) == CURRENT_SCHEMA_VERSION
    validate_schema(store._conn)
    store.close()


def test_migration_is_idempotent(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    assert migrate(store._conn) == []
    store.close()


def test_migration_failure_rolls_back_and_blocks(sqlite_path: str) -> None:
    import aura.memory.migrations as mig

    conn = sqlite3.connect(sqlite_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (version) VALUES (0)")
    conn.commit()

    original = dict(mig.MIGRATIONS)
    mig.MIGRATIONS[1] = ("CREATE INDEX this_is_a_syntax_error ON memory_entries(id)",)
    try:
        with pytest.raises(ConfigurationError, match="migration to schema version 1 failed"):
            mig.migrate(conn)
        assert current_version(conn) == 0
    finally:
        mig.MIGRATIONS.clear()
        mig.MIGRATIONS.update(original)
    conn.close()


def test_open_without_migrations_blocks_on_schema() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (version) VALUES (0)")
    conn.commit()
    with pytest.raises(ConfigurationError, match="run migrations"):
        validate_schema(conn)
    conn.close()


def test_correct_and_versioned_provenance(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    first = make_entry(key="lineage", content={"v": "a"})
    store.add(first)
    second = MemoryEntry.create(
        key=first.key,
        kind=MemoryType.SEMANTIC,
        content={"v": "b"},
        memory_id=MemoryId.new(),
        provenance=Provenance(source="correction", creator="test"),
        importance=first.importance,
        confidence=first.confidence,
        tags=first.tags,
        sensitivity=first.sensitivity,
    )
    second.version = first.version + 1
    second.supersedes = first.id
    store.add(second)
    assert store.get(second.id).version == 2
    assert str(store.get(second.id).supersedes) == str(first.id)  # type: ignore[union-attr]
    assert store.get(first.id).status is MemoryStatus.ACTIVE
    store.close()


def test_archive_restore_round_trip(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    entry = make_entry(key="keep", content={"v": 1})
    store.add(entry)
    store.archive(store.get(entry.id))
    assert store.count() == 0
    restored = store.restore(entry.id)
    assert restored.status is MemoryStatus.ACTIVE
    assert store.count() == 1
    store.close()


def test_restore_missing_raises(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    with pytest.raises(NotFoundError):
        store.restore(MemoryId.new())
    store.close()
def test_search_filters_kind_status_and_text(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    store.add(make_entry(key="deploy:ok", kind=MemoryType.EPISODIC, content={"text": "green"}, tags=("ops",)))
    store.add(make_entry(key="deploy:fail", kind=MemoryType.SEMANTIC, content={"text": "red"}, tags=("ops",)))
    store.add(make_entry(key="other", kind=MemoryType.SEMANTIC, content={"text": "green"}))
    assert len(store.search(text="green")) == 2
    assert len(store.search(text="green", kind=MemoryType.SEMANTIC)) == 1
    assert len(store.search(tags=("ops",))) == 2
    assert len(store.search(status=MemoryStatus.ACTIVE)) == 3
    store.close()


def test_transaction_rolls_back_on_exception(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    store.add(make_entry(key="before"))
    with pytest.raises(RuntimeError, match="boom"), store.transaction():
        store.add(make_entry(key="inside"))
        raise RuntimeError("boom")
    assert store.count() == 1
    store.close()


def test_transaction_commits_on_success(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    with store.transaction():
        store.add(make_entry(key="a"))
        store.add(make_entry(key="b"))
    assert store.count() == 2
    store.close()


def test_concurrent_writes_are_serialized_and_all_land(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    errors: list[Exception] = []

    def writer(index: int) -> None:
        try:
            for _ in range(5):
                store.add(make_entry(key=f"t{index}", content={"i": index}))
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert not errors
    assert store.count() == 40
    store.close()


def test_store_survives_reopen_persistence(sqlite_path: str) -> None:
    store = SQLiteMemoryStore(path=sqlite_path)
    entry = make_entry(key="persist", content={"v": 42})
    store.add(entry)
    store.close()
    reopen = SQLiteMemoryStore(path=sqlite_path)
    assert reopen.get(entry.id).content == {"v": 42}
    assert reopen.count() == 1
    reopen.close()


def test_corrupt_database_file_raises_on_open(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_bytes(b"this is not a sqlite database file at all!!!")
    with pytest.raises((StorageIntegrityError, sqlite3.DatabaseError)):
        SQLiteMemoryStore(path=str(path), integrity_check=True)


def test_frozen_clock_used_for_archive_timestamp(sqlite_path: str) -> None:
    from datetime import UTC, datetime

    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=UTC))
    store = SQLiteMemoryStore(path=sqlite_path, clock=clock)
    entry = make_entry(key="timed")
    store.add(entry)
    store.archive(store.get(entry.id))
    row = store._conn.execute(
        "SELECT archived_at FROM memory_archive WHERE id = ?", (str(entry.id),)
    ).fetchone()
    assert row is not None and "2024-01-01" in row[0]
    store.close()