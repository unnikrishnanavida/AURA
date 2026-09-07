"""Backup & recovery + chaos/failure tests.

Covers Phase 12.3 (backup/restore integrity) and 12.5 (controlled failures:
corrupt DB, storage unavailable, partial transaction rollback, interrupted
write, restart-survival). Every test asserts AURA fails safely — errors are
raised, never silently swallowed — and returns to a consistent state.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aura.memory.sqlite_store import SQLiteMemoryStore
from aura.observability.backup import BackupError, create_backup, restore_backup


def make_store(path: Path) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(path=str(path))


# -- backup / restore ---------------------------------------------------------
def test_backup_creates_consistent_copy_and_manifest(tmp_path: Path) -> None:
    db = tmp_path / "live.sqlite3"
    store = make_store(db)
    _seed_entry(store)
    store.close()

    backup_dir = tmp_path / "backup"
    result = create_backup(db_path=db, backup_dir=backup_dir, instance_id="ci", environment="testing")
    assert result.size_bytes > 0
    manifest = backup_dir / "manifest.json"
    assert manifest.exists()
    assert "schema_version" in manifest.read_text(encoding="utf-8")


def _seed_entry(store: SQLiteMemoryStore) -> object:
    from aura.memory.models import MemoryEntry, MemoryType

    entry = MemoryEntry.create(key="bk", kind=MemoryType.SEMANTIC, content={"v": 1})
    store.add(entry)
    return entry


def test_backup_then_restore_recovers_data(tmp_path: Path) -> None:
    db = tmp_path / "live.sqlite3"
    store = make_store(db)
    entry = _seed_entry(store)
    store.close()

    backup_dir = tmp_path / "backup"
    create_backup(db_path=db, backup_dir=backup_dir)

    # Corrupt/destroy the live database with a *different* path so the WAL
    # sidecars of the closed store do not interfere on Windows.
    restored = tmp_path / "restored.sqlite3"
    restore_backup(backup_path=_newest_backup(backup_dir), db_path=restored)
    reopened = make_store(restored)
    assert reopened.get(entry.id).content == {"v": 1}  # type: ignore[attr-defined]
    reopened.close()


def _newest_backup(backup_dir: Path) -> Path:
    candidates = sorted(backup_dir.glob("aura-*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert candidates
    return candidates[0]


def test_restore_rejects_incompatible_schema(tmp_path: Path) -> None:
    db = tmp_path / "live.sqlite3"
    store = make_store(db)
    store.close()
    backup_dir = tmp_path / "backup"
    create_backup(db_path=db, backup_dir=backup_dir)
    backup_file = _newest_backup(backup_dir)

    # tamper with the schema version to simulate an incompatible backup
    conn = sqlite3.connect(str(backup_file))
    conn.execute("UPDATE schema_version SET version = 99")
    conn.commit()
    conn.close()

    with pytest.raises(BackupError, match="schema version"):
        restore_backup(backup_path=backup_file, db_path=tmp_path / "restored.sqlite3")


def test_restore_requires_existing_backup(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        restore_backup(backup_path=tmp_path / "missing.sqlite3", db_path=tmp_path / "x.sqlite3")


def test_create_backup_missing_db_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        create_backup(db_path=tmp_path / "missing.sqlite3", backup_dir=tmp_path / "b")


# -- chaos / failure ------------------------------------------------------------
def test_corrupt_database_raises_not_silently(tmp_path: Path) -> None:
    db = tmp_path / "corrupt.sqlite3"
    db.write_bytes(b"this is not sqlite")
    with pytest.raises((sqlite3.DatabaseError, Exception)):
        make_store(db)


def test_storage_failure_is_surfaces_in_dependency_health(tmp_path: Path) -> None:
    from aura.api.server import AuraApiServer, ServerConfig

    class BrokenStore:
        def count(self) -> int:
            raise RuntimeError("storage unavailable")

    api = AuraApiServer(config=ServerConfig(host="127.0.0.1", port=0))
    api.aura.brain.memory.store = BrokenStore()  # type: ignore[assignment]
    dependency = api._dependency_health()
    assert dependency["ok"] is False
    assert "storage" in str(dependency.get("error", ""))


def test_partial_transaction_rolls_back(tmp_path: Path) -> None:
    store = make_store(tmp_path / "tx.sqlite3")
    with pytest.raises(RuntimeError), store.transaction():
        store.add(from_aura_memory_entry("a"))
        raise RuntimeError("interrupted write")
    assert store.count() == 0
    store.close()


def from_aura_memory_entry(key: str) -> object:
    from aura.memory.models import MemoryEntry, MemoryType

    return MemoryEntry.create(key=key, kind=MemoryType.SEMANTIC, content={"k": key})


def test_survives_restart_and_retains_lineage(tmp_path: Path) -> None:
    db = tmp_path / "restart.sqlite3"
    store = make_store(db)
    a = _seed_entry(store)
    b = from_aura_memory_entry("second")
    store.add(b)  # type: ignore[arg-type]
    store.close()
    reopened = make_store(db)
    assert reopened.count() == 2
    assert reopened.get(a.id).content == {"v": 1}  # type: ignore[arg-type]
    reopened.close()