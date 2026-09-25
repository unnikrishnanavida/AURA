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
    PostgreSQLAuditLog,
    PostgreSQLSessionStore,
    PostgreSQLStateStore,
)
from aura.foundation.errors import ConfigurationError
from aura.security.audit import AuditLog
from aura.security.spool import AuditSpool

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
def test_audit_durable_lifecycle_and_idempotency(state: PostgreSQLStateStore, tmp_path) -> None:
    """Durable append + idempotent duplicate writes (same event_id -> one row)."""
    log = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))
    first = log.record(
        action="policy.deny",
        actor="int-alice",
        resource="api",
        decision="deny",
        reason="policy",
        event_id="ev-int-lc-1",
        correlation_id="co-int-lc",
        payload={"scopes": ["read"]},
    )
    # Replaying/sending the same logical event must not duplicate the row.
    log.record(
        action="policy.deny",
        actor="int-alice",
        resource="api",
        decision="deny",
        reason="policy",
        event_id="ev-int-lc-1",
        correlation_id="co-int-lc",
        payload={"scopes": ["read"]},
    )
    got = log.entries(actor="int-alice")
    assert len(got) == 1
    assert got[0].action == "policy.deny"
    assert got[0].correlation_id == "co-int-lc"
    assert got[0].payload == {"scopes": ["read"]}
    assert str(got[0].event_id) == "ev-int-lc-1"
    assert got[0].to_dict()["event_id"] == "ev-int-lc-1"
    assert first.event_id is not None
    # The duplicate was idempotent: exactly one stored row for the event.
    assert len(log.entries(event_id="ev-int-lc-1")) == 1


def test_audit_shared_across_instances(state: PostgreSQLStateStore, tmp_path) -> None:
    """Two list instances over the same store see one complete trail."""
    a = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "a"))
    b = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "b"))
    a.record(action="key.issue", actor="int-sys", resource="kid-1", decision="allow", reason="issued", event_id="ev-int-sh-1")
    # The record written by instance A is visible to instance B.
    assert len(b.entries(action="key.issue", actor="int-sys")) == 1
    assert b.entries(event_id="ev-int-sh-1")[0].event_id is not None


def test_audit_filters_actor_decision_since(state: PostgreSQLStateStore, tmp_path) -> None:
    log = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))
    log.record(action="a.1", actor="int-f1", resource="api", decision="allow", reason="r", event_id="ev-int-f-1")
    log.record(action="a.2", actor="int-f2", resource="api", decision="deny", reason="r", event_id="ev-int-f-2")
    # Assertions are scoped to unique actors/events because the module shares
    # one real test database across tests.
    assert len(log.entries(actor="int-f1")) == 1
    assert len(log.entries(actor="int-f2", decision="deny")) == 1
    assert len(log.entries(since="2000-01-01T00:00:00+00:00", actor="int-f1")) == 1
    assert log.entries(actor="int-f1", decision="deny") == []
    assert log.entries(event_id="ev-int-f-2")[0].actor == "int-f2"


def test_audit_replay_spooled_resyncs(state: PostgreSQLStateStore, tmp_path) -> None:
    """A spool left by an instance that lost connectivity is replayed on recovery."""
    spool = AuditSpool(tmp_path / "spool")
    spool.append(
        {
            "event_id": "ev-int-rp-1",
            "action": "x",
            "actor": "int-resync",
            "resource": "api",
            "decision": "allow",
            "reason": "recovered",
            "timestamp": "2026-09-25T10:00:00+00:00",
            "correlation_id": None,
            "payload": {},
        }
    )
    spool.append(
        {
            "event_id": "ev-int-rp-2",
            "action": "x",
            "actor": "int-resync",
            "resource": "api",
            "decision": "deny",
            "reason": "recovered",
            "timestamp": "2026-09-25T10:00:01+00:00",
            "correlation_id": None,
            "payload": {},
        }
    )
    log = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))
    result = log.replay_spooled()
    assert result == {"replayed": 2, "skipped": 0, "remaining": 0}
    assert spool.count() == 0
    assert len(log.entries(actor="int-resync")) == 2
    # A second replay has nothing to drain.
    assert log.replay_spooled() == {"replayed": 0, "skipped": 0, "remaining": 0}


def test_audit_replay_skips_records_already_present(state: PostgreSQLStateStore, tmp_path) -> None:
    """Resync skips (idempotently) records that were already persisted."""
    log = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))
    already = log.record(
        action="x",
        actor="int-dup",
        resource="api",
        decision="deny",
        reason="r",
        event_id="ev-int-dup-1",
        correlation_id="co-dupe",
        payload={"n": 1},
    ).to_dict()
    spool = AuditSpool(tmp_path / "spool")
    spool.append(already)
    result = log.replay_spooled()
    assert result == {"replayed": 0, "skipped": 1, "remaining": 0}
    assert spool.count() == 0
    assert len(log.entries(actor="int-dup")) == 1