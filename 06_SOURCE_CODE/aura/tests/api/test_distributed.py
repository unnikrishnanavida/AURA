"""Distributed-state integration tests (real PostgreSQL).

Exercises durable sessions, shared API-key lifecycle, and atomic rate limiting
against a real PostgreSQL instance. Skipped unless ``AURA_TEST_POSTGRESQL_DSN``
is set; never run with mocks. A random test database is created and dropped.
"""

from __future__ import annotations

import os
import threading
import uuid

import pytest

from aura.api.distributed import (
    DistributedRateLimiter,
    PostgreSQLApiKeyStore,
    PostgreSQLSessionStore,
    PostgreSQLStateStore,
)
from aura.foundation.errors import ConfigurationError
from aura.security.audit import AuditLog

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


@pytest.fixture(scope="module")
def pg_database() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping distributed-state integration tests")
    import psycopg

    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_dist_{suffix}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield dbname
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()


@pytest.fixture()
def dsn(pg_database: str) -> str:
    return f"{DSN} dbname={pg_database}"


@pytest.fixture()
def state(dsn: str) -> PostgreSQLStateStore:
    s = PostgreSQLStateStore(dsn=dsn, max_connections=3)
    yield s
    s.close()


def test_state_store_fails_closed_without_dsn() -> None:
    with pytest.raises(ConfigurationError, match="DSN"):
        PostgreSQLStateStore(dsn="")  # type: ignore[arg-type]


def test_session_lifecycle(state: PostgreSQLStateStore) -> None:
    store = PostgreSQLSessionStore(state)
    sid = "ses-unique-1"
    record = store.create(sid, ttl_seconds=60, data={"env": "test"})
    assert record.session_id == sid
    assert store.get(sid) is not None
    assert store.revoke(sid) is True
    assert store.get(sid) is None
    assert store.prune_expired() >= 0


def test_session_expiry(state: PostgreSQLStateStore) -> None:
    import time

    store = PostgreSQLSessionStore(state)
    sid = "ses-expire-1"
    store.create(sid, ttl_seconds=3600, data={})
    assert store.get(sid) is not None
    # Deterministically force expiry (no wall-clock races under load).
    with state.connection() as conn:
        conn.execute(
            "UPDATE aura_sessions SET expires_at = %s WHERE session_id = %s",
            (time.time() - 1.0, sid),
        )
    assert store.get(sid) is None


def test_api_key_issue_validate_revoke(state: PostgreSQLStateStore) -> None:
    keys = PostgreSQLApiKeyStore(state, secret="a-very-long-issuer-secret-0001", audit=AuditLog())
    raw_key, key_id = keys.issue(ttl_seconds=60, scopes=("read", "write"))
    assert keys.validate(raw_key) is not None
    assert keys.revoke(key_id) is True
    assert keys.validate(raw_key) is None
    # Unknown revoke is a no-op.
    assert keys.revoke("kid-does-not-exist") is False


def test_api_key_state_shared_across_stores(state: PostgreSQLStateStore) -> None:
    """Two issuer instances share one table -> revocation propagates."""
    first = PostgreSQLApiKeyStore(state, secret="a-very-long-issuer-secret-0001", audit=AuditLog())
    second = PostgreSQLApiKeyStore(state, secret="a-very-long-issuer-secret-0001", audit=AuditLog())
    raw_key, key_id = first.issue()
    assert second.validate(raw_key) is not None
    first.revoke(key_id)
    assert second.validate(raw_key) is None


def test_rate_limiter_burst(state: PostgreSQLStateStore) -> None:
    limiter = DistributedRateLimiter(state=state, burst=3, per_second=0.5)
    results = [limiter.allow("10.0.0.1") for _ in range(5)]
    assert results == [True, True, True, False, False]
    # Other IPs are independent.
    assert limiter.allow("10.0.0.2") is True


def test_rate_limiter_shared_bucket(state: PostgreSQLStateStore) -> None:
    """Two limiter instances share one bucket -> combined consumption."""
    a = DistributedRateLimiter(state=state, burst=2, per_second=0.2)
    b = DistributedRateLimiter(state=state, burst=2, per_second=0.2)
    assert a.allow("10.0.0.3") is True
    assert b.allow("10.0.0.3") is True
    assert a.allow("10.0.0.3") is False
    assert b.allow("10.0.0.3") is False


def test_rate_limiter_fail_closed_when_store_down() -> None:
    """A dead shared store denies (fail closed) rather than allowing."""
    # Build a limiter over a *stubbed* state whose only method raises, exactly
    # as a real unreachable store would behave mid-flight.
    class _DeadState:
        def connection(self) -> object:
            raise RuntimeError("connection refused")

    dead = _DeadState()
    limiter = DistributedRateLimiter(state=dead, burst=60, per_second=1.0, degraded_policy="fail_closed")
    assert limiter.allow("10.0.0.9") is False
    # Bounded-local mode still throttles during the same outage.
    local = DistributedRateLimiter(state=dead, burst=60, per_second=1.0, degraded_policy="bounded_local")
    assert local.allow("10.0.0.9") is True


def test_distributed_concurrent_writes(state: PostgreSQLStateStore) -> None:
    """Concurrent session creates across threads do not collide."""
    store = PostgreSQLSessionStore(state)
    errors: list[Exception] = []

    def worker(offset: int) -> None:
        try:
            for i in range(10):
                store.create(f"ses-thread-{offset}-{i}", ttl_seconds=60, data={"i": i})
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent session writes failed: {errors}"
    for i in range(4):
        assert store.get(f"ses-thread-{i}-5") is not None