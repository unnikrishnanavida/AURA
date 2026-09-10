"""Upgrade-path verification for the PostgreSQL memory store (Phase 16/19).

Proves forward migrations from a controlled "old" schema without fabricating
release history: we create a v0-style database (empty, no tables), then open
the store which must migrate to the current schema, and verify a future /
incompatible schema is refused rather than silently modified.
"""

from __future__ import annotations

import os
import uuid

import pytest

from aura.memory import pg_migrations
from aura.memory.postgresql_store import PostgreSQLMemoryStore

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


@pytest.fixture(scope="module")
def fresh_db() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping upgrade-path tests")
    import psycopg

    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_upg_{suffix}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield f"{DSN} dbname={dbname}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()


def test_migration_from_blank_db_upgrades_schema(fresh_db: str) -> None:
    """A fresh (v0 / no tables) database is migrated to the current version."""
    store = PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2)
    try:
        import psycopg

        with psycopg.connect(fresh_db, connect_timeout=5) as conn:
            assert pg_migrations.current_version(conn) == pg_migrations.CURRENT_SCHEMA_VERSION
        # The live table exists and is usable.
        assert store.count() == 0
    finally:
        store.close()


def test_data_preserved_across_migration(fresh_db: str) -> None:
    """Data written after migration is durable and readable on re-open."""
    store = PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2)
    from aura.foundation.ids import MemoryId
    from aura.memory.models import MemoryEntry, MemoryType, Provenance, Sensitivity, MemoryConfidence

    entry = MemoryEntry(
        id=MemoryId.new(),
        key="upgrade-key",
        kind=MemoryType.SEMANTIC,
        content={"text": "survives upgrade"},
        confidence=MemoryConfidence(),
        provenance=Provenance(source="test", creator="upgrade"),
        sensitivity=Sensitivity.INTERNAL,
    )
    store.add(entry)
    store.close()

    # Re-open (simulates running the "new" version against migrated data).
    store = PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2, run_migrations=True)
    try:
        got = store.get(entry.id)
        assert got.key == "upgrade-key"
        assert got.content["text"] == "survives upgrade"
    finally:
        store.close()


def test_future_schema_is_refused_without_mutation(fresh_db: str) -> None:
    """A newer-than-known schema is refused and never silently modified."""
    store = PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2)
    store.close()

    import psycopg

    from aura.foundation.errors import ConfigurationError

    with psycopg.connect(fresh_db, connect_timeout=5) as conn:
        conn.execute(f"UPDATE {pg_migrations.SCHEMA_TABLE} SET version = {pg_migrations.CURRENT_SCHEMA_VERSION + 100}")

    with pytest.raises(ConfigurationError):
        PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2)

    # The schema version row was NOT touched.
    with psycopg.connect(fresh_db, connect_timeout=5) as conn:
        assert pg_migrations.current_version(conn) == pg_migrations.CURRENT_SCHEMA_VERSION + 100