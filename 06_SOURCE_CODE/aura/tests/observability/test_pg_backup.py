"""PostgreSQL backup/restore integration tests (real PostgreSQL).

Skipped unless ``AURA_TEST_POSTGRESQL_DSN`` is set. Uses a disposable database.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryConfidence, MemoryEntry, MemoryType, Provenance, Sensitivity
from aura.memory.postgresql_store import PostgreSQLMemoryStore
from aura.observability.pg_backup import (
    PgBackupError,
    create_pg_backup,
    restore_pg_backup,
)

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


@pytest.fixture(scope="module")
def pg_database() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping PG backup tests")
    import psycopg

    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_bk_{suffix}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield f"{DSN} dbname={dbname}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()


def test_pg_backup_and_restore_roundtrip(pg_database: str) -> None:
    store = PostgreSQLMemoryStore(dsn=pg_database, max_connections=3)
    entry = MemoryEntry(
        id=MemoryId.new(),
        key="pg-backup-key",
        kind=MemoryType.SEMANTIC,
        content={"text": "backup me"},
        importance=0.5,
        confidence=MemoryConfidence(),
        provenance=Provenance(source="test", creator="pytest"),
        sensitivity=Sensitivity.INTERNAL,
    )
    store.add(entry)
    store.close()

    tmp = Path(tempfile.mkdtemp(prefix="pg-backup-"))
    result = create_pg_backup(
        dsn=pg_database,
        backup_dir=str(tmp),
        instance_id="test",
        environment="testing",
    )
    assert Path(result.path).exists()
    assert (tmp / "manifest.json").exists()

    # CLOBBER protection: restoring onto a populated target refuses.
    store = PostgreSQLMemoryStore(dsn=pg_database, max_connections=3)
    store.add(
        MemoryEntry(
            id=MemoryId.new(),
            key="other",
            kind=MemoryType.SEMANTIC,
            content={"x": 1},
            confidence=MemoryConfidence(),
            provenance=Provenance(source="t", creator="c"),
            sensitivity=Sensitivity.PUBLIC,
        )
    )
    store.close()
    with pytest.raises(PgBackupError, match="target already has"):
        restore_pg_backup(backup_path=result.path, dsn=pg_database)

    # Force-restore replaces only AURA tables.
    counts = restore_pg_backup(backup_path=result.path, dsn=pg_database, force=True)
    assert counts["memory_entries"] == 1

    reopened = PostgreSQLMemoryStore(dsn=pg_database, max_connections=2, run_migrations=False)
    try:
        found = reopened.search(text="backup me")
        assert any(e.key == "pg-backup-key" for e in found)
    finally:
        reopened.close()


def test_pg_backup_creates_missing_backup_dir(pg_database: str) -> None:
    """A fresh (non-existent) backup_dir must be created, not crash (P28-5)."""
    root = Path(tempfile.mkdtemp(prefix="pg-backup-mkdir-"))
    fresh = root / "nested" / "backups"  # does not exist yet
    assert not fresh.exists()
    result = create_pg_backup(
        dsn=pg_database,
        backup_dir=str(fresh),
        instance_id="test",
        environment="testing",
    )
    assert Path(result.path).exists()
    assert (fresh / "manifest.json").exists()
    assert result.size_bytes > 0
def test_pg_backup_rejects_non_aura_file(pg_database: str) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="pg-backup-"))
    bad = tmp / "bad.sql"
    bad.write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(PgBackupError, match="not an AURA logical backup"):
        restore_pg_backup(backup_path=bad, dsn=pg_database)