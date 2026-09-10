"""Real PostgreSQL integration tests for the memory store.

These tests exercise a **real** PostgreSQL instance and are skipped unless
``AURA_TEST_POSTGRESQL_DSN`` points at a reachable server. They are never run
with mocks. Test databases are created per-session with a random suffix and
dropped at teardown, so runs do not clobber production data.

Example:

    set AURA_TEST_POSTGRESQL_DSN=host=127.0.0.1 port=55432 dbname=postgres user=aura password=...
    python -m pytest tests/memory/test_pg_store.py -q
"""

from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Iterator

import pytest

from aura.foundation.errors import ConfigurationError, NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory import pg_migrations
from aura.memory.models import (
    MemoryConfidence,
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    Provenance,
    Sensitivity,
)
from aura.memory.postgresql_store import PostgreSQLMemoryStore

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


def _admin_conn() -> object:
    import psycopg

    return psycopg.connect(DSN, connect_timeout=5)


def _make_entry(*, key: str = "pg-key", kind: MemoryType = MemoryType.SEMANTIC, content: dict | None = None) -> MemoryEntry:
    return MemoryEntry(
        id=MemoryId.new(),
        key=key,
        kind=kind,
        content=content or {"text": key},
        importance=0.5,
        confidence=MemoryConfidence(),
        provenance=Provenance(source="test", creator="pytest"),
        sensitivity=Sensitivity.INTERNAL,
    )


@pytest.fixture(scope="module")
def pg_database() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping real-PostgreSQL integration tests")
    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_test_{suffix}"
    conn = _admin_conn()  # type: ignore[arg-type]
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield dbname
    conn = _admin_conn()  # type: ignore[arg-type]
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()
@pytest.fixture()
def store(pg_database: str) -> PostgreSQLMemoryStore:
    dsn = f"{DSN} dbname={pg_database}"
    s = PostgreSQLMemoryStore(dsn=dsn, max_connections=3)
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _reset_schema(pg_database: str) -> Iterator[None]:
    """Reset the shared test database between tests so counts never leak.

    Drops the live tables and clears the version row; the next
    ``PostgreSQLMemoryStore`` open re-runs migrations deterministically
    (CREATE TABLE IF NOT EXISTS idempotent).
    """
    yield
    import psycopg

    dsn = f"{DSN} dbname={pg_database}"
    try:
        with psycopg.connect(dsn) as conn:
            conn.execute("DROP TABLE IF EXISTS memory_entries")
            conn.execute("DROP TABLE IF EXISTS memory_archive")
            conn.execute(f"DELETE FROM {pg_migrations.SCHEMA_TABLE}")
    except Exception:
        # schema may not exist at all yet (e.g. connection-failure test); ignore
        pass


def test_migrations_apply_and_validate(pg_database: str) -> None:
    dsn = f"{DSN} dbname={pg_database}"
    s = PostgreSQLMemoryStore(dsn=dsn, max_connections=2)
    s.close()
    import psycopg

    with psycopg.connect(dsn) as conn:
        assert pg_migrations.current_version(conn) == pg_migrations.CURRENT_SCHEMA_VERSION
        row = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'memory_entries'"
        ).fetchone()
        assert row is not None and row[0] == 1


def test_create_read_update_delete(store: PostgreSQLMemoryStore) -> None:
    entry = _make_entry(key="crud-key")
    store.add(entry)
    assert store.get(entry.id).key == "crud-key"
    assert store.count() == 1

    entry.content = {"text": "changed"}
    store.update(entry)
    assert store.get(entry.id).content["text"] == "changed"

    store.delete(entry.id)
    with pytest.raises(NotFoundError):
        store.get(entry.id)
    assert store.count() == 0


def test_search_filters(store: PostgreSQLMemoryStore) -> None:
    a = _make_entry(key="alpha-key", kind=MemoryType.SEMANTIC)
    b = _make_entry(key="beta-key", kind=MemoryType.EPISODIC)
    store.add(a)
    store.add(b)

    assert len(store.search(text="alpha")) == 1
    assert len(store.search(kind=MemoryType.SEMANTIC)) == 1
    assert store.search(text="alpha", kind=MemoryType.SEMANTIC)[0].id == a.id
    assert store.search(status=MemoryStatus.ACTIVE) == [a, b]
def test_archive_and_restore(store: PostgreSQLMemoryStore) -> None:
    entry = _make_entry(key="archive-me")
    store.add(entry)
    store.archive(entry)
    assert store.count() == 0
    with pytest.raises(NotFoundError):
        store.get(entry.id)

    restored = store.restore(entry.id)
    assert restored.status == MemoryStatus.ACTIVE
    assert store.get(entry.id).key == "archive-me"
    assert store.count() == 1


def test_restore_missing_raises(store: PostgreSQLMemoryStore) -> None:
    with pytest.raises(NotFoundError):
        store.restore(MemoryId.new())


def test_transaction_rolls_back_on_failure(store: PostgreSQLMemoryStore) -> None:
    entry = _make_entry(key="txn-key")
    store.add(entry)

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom), store.transaction():
        store.delete(entry.id)
        raise Boom("simulated partial failure")

    assert store.get(entry.id).key == "txn-key"
    assert store.count() == 1


def test_concurrent_writes(store: PostgreSQLMemoryStore) -> None:
    errors: list[Exception] = []

    def writer(index: int) -> None:
        try:
            for _ in range(10):
                entry = _make_entry(key=f"conc-{index}")
                store.add(entry)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent writes failed: {errors}"
    assert store.count() == 40


def test_restart_survival(pg_database: str) -> None:
    dsn = f"{DSN} dbname={pg_database}"
    first = PostgreSQLMemoryStore(dsn=dsn, max_connections=2)
    entry = _make_entry(key="persist-survives")
    first.add(entry)
    first.close()

    second = PostgreSQLMemoryStore(dsn=dsn, max_connections=2)
    try:
        assert second.get(entry.id).key == "persist-survives"
    finally:
        second.close()


def test_connection_failure_is_explicit(pg_database: str) -> None:
    bad_dsn = (
        f"host=127.0.0.1 port=1 dbname={pg_database} "
        "user=aura password=wrong connect_timeout=1"
    )
    with pytest.raises(ConfigurationError):
        PostgreSQLMemoryStore(dsn=bad_dsn)


def test_incompatible_schema_refuses_startup(pg_database: str) -> None:
    import psycopg

    dsn = f"{DSN} dbname={pg_database}"
    # Establish a known-good schema first.
    s = PostgreSQLMemoryStore(dsn=dsn, max_connections=2)
    s.close()

    # Simulate a newer/incompatible schema: table dropped and version bumped
    # beyond anything this build knows, so no forward migration applies and
    # startup must refuse rather than guess.
    with psycopg.connect(dsn) as conn:
        conn.execute("DROP TABLE memory_entries")
        conn.execute("DELETE FROM memory_archive")
        conn.execute(f"UPDATE {pg_migrations.SCHEMA_TABLE} SET version = 999")

    with pytest.raises(ConfigurationError, match="999"):
        PostgreSQLMemoryStore(dsn=dsn)


def test_corrupted_row_raises_when_read(pg_database: str) -> None:
    import psycopg

    dsn = f"{DSN} dbname={pg_database}"
    s = PostgreSQLMemoryStore(dsn=dsn, max_connections=2)
    entry = _make_entry(key="corrupt-me")
    s.add(entry)

    with psycopg.connect(dsn) as conn:
        conn.execute(
            "UPDATE memory_entries SET created_at = 'NOT-A-TIMESTAMP' WHERE id = %s",
            (str(entry.id),),
        )

    with pytest.raises(ValueError, match="corrupted"):
        s.get(entry.id)
    s.close()