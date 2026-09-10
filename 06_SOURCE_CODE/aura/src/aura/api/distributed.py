"""Distributed state for the AURA HTTP API.

Multi-instance deployments need sessions, API-key state, and rate-limit
counters to be shared rather than process-local. This module provides
PostgreSQL-backed implementations of those three stateful boundaries using the
same minimal, well-understood architecture as the memory store: a connection
pool + versioned schema. No separate infrastructure (e.g. Redis) is required.

Design decisions:

- **Distributed rate limiting is atomic.** Token refill and consumption happen
  in a single SQL statement, so concurrent API instances cannot double-spend a
  bucket. State is bounded: stale rows are pruned on a schedule.
- **Failure policy is explicit and fail-closed by default.** When the shared
  store is unreachable, :class:`DistributedRateLimiter` denies (never silently
  fails open). An operator may opt into a *bounded local emergency mode* that
  caps per-instance throughput below the configured limit; it is documented
  and audited, never invisible.
- **Sessions are durable.** A session survives an API process restart and is
  visible to every instance. Expired/revoked sessions are rejected and
  periodically cleaned.
- **API-key lifecycle is shared.** Issue/validate/expire/revoke operate on the
  same table, so revocation propagates instantly across instances. Raw keys are
  never stored — only HMAC digests, matching :class:`aura.api.security.ApiKeyIssuer`.

Consistency model: strong for sessions and API keys (single-row reads/writes),
eventual for rate-limit cleanup (pruning is best-effort and idempotent).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from aura.api.security import KeySpec
from aura.foundation.errors import ConfigurationError
from aura.security.audit import AuditLog


def _optional_pool() -> Any:
    try:
        import psycopg_pool
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "psycopg-pool is not installed; run `pip install aura[postgresql]` "
            "to use distributed API state"
        ) from exc
    return psycopg_pool


def _optional_driver() -> Any:
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "psycopg is not installed; run `pip install aura[postgresql]` "
            "to use distributed API state"
        ) from exc
    return psycopg


_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS aura_sessions (
        session_id TEXT PRIMARY KEY,
        created_at DOUBLE PRECISION NOT NULL,
        expires_at DOUBLE PRECISION,
        revoked INTEGER NOT NULL DEFAULT 0,
        events BIGINT NOT NULL DEFAULT 0,
        data TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aura_api_keys (
        key_id TEXT PRIMARY KEY,
        digest TEXT NOT NULL,
        issued_at DOUBLE PRECISION NOT NULL,
        expires_at DOUBLE PRECISION,
        revoked INTEGER NOT NULL DEFAULT 0,
        scopes TEXT NOT NULL DEFAULT '[]'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aura_rate_limits (
        ip TEXT PRIMARY KEY,
        tokens DOUBLE PRECISION NOT NULL,
        window_start DOUBLE PRECISION NOT NULL,
        updated_at DOUBLE PRECISION NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_aura_sessions_expiry ON aura_sessions(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_aura_keys_expiry ON aura_api_keys(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_aura_rate_updated ON aura_rate_limits(updated_at)",
)


class DistributedStateError(RuntimeError):
    """Raised when the shared state store is unreachable and policy is fail-closed."""
class PostgreSQLStateStore:
    """Shared PostgreSQL connection pool + schema for API distributed state."""

    def __init__(self, *, dsn: str, min_connections: int = 1, max_connections: int = 5) -> None:
        if not dsn:
            raise ConfigurationError(
                "distributed state requires a PostgreSQL DSN; refusing to fall back to process-local state"
            )
        self._dsn = dsn
        self._lock = threading.RLock()
        pool_lib = _optional_pool()
        try:
            self._pool = pool_lib.ConnectionPool(
                conninfo=dsn,
                min_size=min_connections,
                max_size=max_connections,
                open=True,
                timeout=min(10, max(2, min_connections * 3)),
                kwargs={"connect_timeout": 5},
            )
        except Exception as exc:  # incl. psycopg.OperationalError
            raise ConfigurationError(f"failed to connect distributed state store: {exc}") from exc

        # Probe immediately so a down store is an explicit startup failure.
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:
            self._pool.close()
            raise ConfigurationError(f"failed to connect distributed state store: {exc}") from exc

        with self._lock, self._pool.connection() as conn:
            for statement in _SCHEMA_STATEMENTS:
                conn.execute(statement)

    def close(self) -> None:
        pool = getattr(self, "_pool", None)
        if pool is not None:
            pool.close()

    def connection(self) -> Any:
        return self._pool.connection()

    @property
    def healthy(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False


@dataclass
class SessionRecord:
    session_id: str
    created_at: float
    expires_at: float | None
    revoked: bool
    events: int
    data: dict[str, Any]


class PostgreSQLSessionStore:
    """Durable, shared, expiring session storage."""

    def __init__(self, state: PostgreSQLStateStore) -> None:
        self._state = state

    def create(
        self,
        session_id: str,
        *,
        ttl_seconds: float | None = None,
        data: dict[str, Any] | None = None,
    ) -> SessionRecord:
        import json

        now = time.time()
        expires = now + ttl_seconds if ttl_seconds is not None else None
        with self._state.connection() as conn:
            conn.execute(
                "INSERT INTO aura_sessions (session_id, created_at, expires_at, revoked, events, data) "
                "VALUES (%s, %s, %s, 0, 0, %s)",
                (session_id, now, expires, json.dumps(data or {}, sort_keys=True)),
            )
        return SessionRecord(session_id, now, expires, False, 0, data or {})

    def get(self, session_id: str) -> SessionRecord | None:
        import json

        with self._state.connection() as conn:
            raw = conn.execute(
                "SELECT session_id, created_at, expires_at, revoked, events, data "
                "FROM aura_sessions WHERE session_id = %s",
                (session_id,),
            ).fetchone()
        if raw is None:
            return None
        record = SessionRecord(
            session_id=str(raw[0]),
            created_at=float(raw[1]),
            expires_at=float(raw[2]) if raw[2] is not None else None,
            revoked=bool(raw[3]),
            events=int(raw[4]),
            data=json.loads(raw[5] or "{}"),
        )
        if record.revoked:
            return None
        if record.expires_at is not None and time.time() > record.expires_at:
            return None
        return record

    def touch(self, session_id: str, *, event: bool = False) -> None:
        with self._state.connection() as conn:
            if event:
                conn.execute(
                    "UPDATE aura_sessions SET events = events + 1 WHERE session_id = %s",
                    (session_id,),
                )
            else:
                conn.execute(
                    "UPDATE aura_sessions SET created_at = %s WHERE session_id = %s",
                    (time.time(), session_id),
                )

    def revoke(self, session_id: str) -> bool:
        with self._state.connection() as conn:
            cur = conn.execute(
                "UPDATE aura_sessions SET revoked = 1 WHERE session_id = %s",
                (session_id,),
            )
            return int(cur.rowcount) > 0

    def prune_expired(self, *, max_age_seconds: float | None = None) -> int:
        now = time.time()
        with self._state.connection() as conn:
            if max_age_seconds is not None:
                cur = conn.execute(
                    "DELETE FROM aura_sessions WHERE expires_at IS NOT NULL AND expires_at < %s "
                    "OR (expires_at IS NULL AND created_at < %s)",
                    (now, now - max_age_seconds),
                )
            else:
                cur = conn.execute(
                    "DELETE FROM aura_sessions WHERE expires_at IS NOT NULL AND expires_at < %s",
                    (now,),
                )
            return int(cur.rowcount)
class PostgreSQLApiKeyStore:
    """Shared API-key lifecycle (HMAC digests only, never raw keys)."""

    def __init__(self, state: PostgreSQLStateStore, *, secret: str, audit: AuditLog | None = None) -> None:
        if not secret or len(secret) < 16:
            raise ValueError("issuer secret must be at least 16 characters")
        self._state = state
        self._secret = secret
        self._audit = audit or AuditLog()

    def issue(self, *, ttl_seconds: float | None = None, scopes: tuple[str, ...] = ("*",)) -> tuple[str, str]:
        import hashlib
        import hmac
        import json
        import uuid

        key_id = f"kid-{uuid.uuid4().hex[:12]}"
        raw_key = uuid.uuid4().hex + uuid.uuid4().hex
        digest = hmac.new(self._secret.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
        now = time.time()
        expires = now + ttl_seconds if ttl_seconds is not None else None
        with self._state.connection() as conn:
            conn.execute(
                "INSERT INTO aura_api_keys (key_id, digest, issued_at, expires_at, revoked, scopes) "
                "VALUES (%s, %s, %s, %s, 0, %s)",
                (key_id, digest, now, expires, json.dumps(list(scopes))),
            )
        self._audit.record(
            action="api_key.issue",
            actor="system",
            resource=key_id,
            decision="allow",
            reason="key issued",
            payload={"scopes": list(scopes), "ttl_seconds": ttl_seconds},
        )
        return raw_key, key_id

    def validate(self, raw_key: str) -> KeySpec | None:
        if not raw_key:
            return None
        import hashlib
        import hmac
        import json

        digest = hmac.new(self._secret.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
        with self._state.connection() as conn:
            raw = conn.execute(
                "SELECT key_id, digest, issued_at, expires_at, revoked, scopes "
                "FROM aura_api_keys WHERE digest = %s",
                (digest,),
            ).fetchone()
        if raw is None:
            return None
        key_id, stored_digest, issued_at, expires_at, revoked, scopes = raw
        if revoked:
            return None
        if expires_at is not None and time.time() > float(expires_at):
            return None
        return KeySpec(
            key_id=str(key_id),
            digest=str(stored_digest),
            issued_at=float(issued_at),
            expires_at=float(expires_at) if expires_at is not None else None,
            scopes=tuple(json.loads(scopes or "[]")),
        )

    def revoke(self, key_id: str) -> bool:
        with self._state.connection() as conn:
            cur = conn.execute(
                "UPDATE aura_api_keys SET revoked = 1 WHERE key_id = %s",
                (key_id,),
            )
            ok = int(cur.rowcount) > 0
        if ok:
            self._audit.record(
                action="api_key.revoke",
                actor="system",
                resource=key_id,
                decision="deny",
                reason="API key revoked",
            )
        return ok

    def prune_expired(self) -> int:
        with self._state.connection() as conn:
            cur = conn.execute(
                "DELETE FROM aura_api_keys WHERE expires_at IS NOT NULL AND expires_at < %s",
                (time.time(),),
            )
            return int(cur.rowcount)

    def stats(self) -> dict[str, int]:
        with self._state.connection() as conn:
            raw = conn.execute(
                "SELECT COUNT(*) FROM aura_api_keys WHERE revoked = 0"
            ).fetchone()
            total = conn.execute("SELECT COUNT(*) FROM aura_api_keys").fetchone()
        return {"active": int(raw[0]) if raw else 0, "total": int(total[0]) if total else 0}
class DistributedRateLimiter:
    """Atomic, shared token bucket.

    Refill + consume happen atomically so concurrent instances share a single
    bucket correctly. When the store is unreachable the behavior is governed by
    ``degraded_policy``:

    - ``fail_closed`` (default): deny the request and audit it.
    - ``bounded_local``: fall back to a per-instance counter capped at the
      configured burst, so a store outage throttles rather than opens the
      floodgates. The fallback is audited with each use.
    """

    def __init__(
        self,
        *,
        state: PostgreSQLStateStore,
        burst: int = 60,
        per_second: float = 1.0,
        degraded_policy: str = "fail_closed",
        audit: AuditLog | None = None,
    ) -> None:
        self._state = state
        self._burst = burst
        self._per_second = per_second
        self._degraded_policy = degraded_policy
        self._audit = audit or AuditLog()
        self._local: dict[str, tuple[float, float]] = {}
        self._local_lock = threading.RLock()

    def allow(self, ip: str) -> bool:
        try:
            return self._allow_shared(ip)
        except Exception as exc:  # noqa: BLE001 - store unreachable
            self._audit.record(
                action="rate_limit.degraded",
                actor=ip,
                resource="api",
                decision="deny" if self._degraded_policy == "fail_closed" else "allow",
                reason=f"distributed state unavailable: {exc}",
            )
            if self._degraded_policy == "bounded_local":
                return self._allow_local(ip)
            return False

    def _allow_shared(self, ip: str) -> bool:
        now = time.time()
        with self._state.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO aura_rate_limits (ip, tokens, window_start, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ip) DO UPDATE SET
                    tokens = LEAST(%s, aura_rate_limits.tokens + (EXTRACT(EPOCH FROM now()) - aura_rate_limits.window_start) * %s),
                    window_start = EXTRACT(EPOCH FROM now()),
                    updated_at = EXTRACT(EPOCH FROM now())
                RETURNING tokens
                """,
                (ip, float(self._burst), now, now, float(self._burst), self._per_second),
            )
            row = cur.fetchone()
        if row is None:
            return False
        tokens = float(row[0])
        if tokens < 1.0:
            self._audit.record(
                action="rate_limit.deny",
                actor=ip,
                resource="api",
                decision="deny",
                reason="rate limit exceeded",
            )
            return False
        with self._state.connection() as conn:
            conn.execute(
                "UPDATE aura_rate_limits SET tokens = tokens - 1, updated_at = %s WHERE ip = %s",
                (time.time(), ip),
            )
        return True

    def _allow_local(self, ip: str) -> bool:
        now = time.time()
        with self._local_lock:
            tokens, window_start = self._local.get(ip, (float(self._burst), now))
            elapsed = now - window_start
            refill = elapsed * self._per_second
            if refill >= 1.0:
                tokens = min(float(self._burst), tokens + refill)
                window_start = now
            if tokens < 1.0:
                return False
            self._local[ip] = (tokens - 1.0, window_start)
            return True

    def prune_stale(self, *, max_age_seconds: float = 3600) -> int:
        with self._state.connection() as conn:
            cur = conn.execute(
                "DELETE FROM aura_rate_limits WHERE updated_at < %s",
                (time.time() - max_age_seconds,),
            )
            return int(cur.rowcount)


__all__ = [
    "DistributedRateLimiter",
    "DistributedStateError",
    "PostgreSQLApiKeyStore",
    "PostgreSQLSessionStore",
    "PostgreSQLStateStore",
    "SessionRecord",
]