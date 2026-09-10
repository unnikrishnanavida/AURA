"""Concurrent migration safety tests for the PostgreSQL memory store.

Real-PostgreSQL test proving multiple store instances can initialize against
the same fresh database simultaneously without catalog ``UniqueViolation``
races (the fix is a migration advisory lock).
"""

from __future__ import annotations

import os
import threading
import uuid

import pytest

from aura.memory.postgresql_store import PostgreSQLMemoryStore

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


@pytest.fixture(scope="module")
def fresh_db() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping concurrent migration tests")
    import psycopg

    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_conc_{suffix}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield f"{DSN} dbname={dbname}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()


def test_concurrent_migrations_across_stores(fresh_db: str) -> None:
    """Several stores opening the same fresh DB concurrently must not race."""
    errors: list[Exception] = []
    stores: list[PostgreSQLMemoryStore] = []

    def open_store() -> None:
        try:
            stores.append(PostgreSQLMemoryStore(dsn=fresh_db, max_connections=2))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=open_store) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent migration raced: {errors}"
    assert len(stores) == 6, f"expected 6 open stores, got {len(stores)}"
    for store in stores:
        # The fixed migration lock must also leave a readable schema.
        assert store.count() == 0
        store.close()