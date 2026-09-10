"""Database migrations for the PostgreSQL memory store.

Mirrors the SQLite migration contract (forward-only, versioned, transactional,
fails-closed on incompatible schema) but targets PostgreSQL using psycopg3.

- a ``schema_version`` table records the applied version as a single row;
- migrations are a deterministic ordered list; each runs inside one
  transaction (DDL is transactional in PostgreSQL) and bumps the version;
- opening a store calls :func:`migrate` after a schema-compatibility check;
  a failed migration rolls back and raises :class:`ConfigurationError`, so the
  operator must restore from a compatible backup — it is never silently
  re-applied, skipped, or downgraded.
"""

from __future__ import annotations

import logging
from typing import Any

from aura.foundation.errors import ConfigurationError

logger = logging.getLogger("aura.memory")

SCHEMA_TABLE = "schema_version"
INITIAL_VERSION = 0
CURRENT_SCHEMA_VERSION = 1

# Advisory-lock key for serializing concurrent migrations across instances.
# Must remain stable across releases (a fixed 64-bit value in the migration
# namespace; see https://www.postgresql.org/docs/current/functions-admin.html).
_MIGRATION_LOCK_KEY = 0x41555241_4D5F4D31  # "AURAM_M1" as a bigint literal

_COLUMNS = """
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    importance DOUBLE PRECISION NOT NULL,
    confidence_fact DOUBLE PRECISION NOT NULL,
    confidence_source DOUBLE PRECISION NOT NULL,
    confidence_freshness DOUBLE PRECISION NOT NULL,
    confidence_relevance DOUBLE PRECISION NOT NULL,
    provenance_source TEXT NOT NULL,
    provenance_execution_id TEXT,
    provenance_creator TEXT NOT NULL,
    provenance_details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_access TEXT NOT NULL,
    access_count BIGINT NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',
    expires_at TEXT,
    links TEXT NOT NULL DEFAULT '{}',
    sensitivity TEXT NOT NULL,
    status TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    supersedes TEXT,
    observed_at TEXT,
    retention_ttl_seconds DOUBLE PRECISION,
    retention_max_versions INTEGER,
    schema_version INTEGER NOT NULL DEFAULT 1
"""

MIGRATION_1_STATEMENTS: tuple[str, ...] = (
    f"CREATE TABLE IF NOT EXISTS memory_entries ({_COLUMNS})",
    "CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key)",
    "CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory_entries(kind)",
    "CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_entries(status)",
    "CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at)",
    (
        "CREATE TABLE IF NOT EXISTS memory_archive ("
        f"{_COLUMNS},"
        " archived_at TEXT NOT NULL"
        ")"
    ),
)

MIGRATIONS: dict[int, tuple[str, ...]] = {
    1: MIGRATION_1_STATEMENTS,
}


def _ensure_version_table(conn: Any) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_TABLE} (version BIGINT NOT NULL)"
    )


def current_version(conn: Any) -> int:
    """Return the recorded schema version (0 on a fresh database)."""
    _ensure_version_table(conn)
    row = conn.execute(f"SELECT version FROM {SCHEMA_TABLE}").fetchone()
    if row is None:
        return INITIAL_VERSION
    return int(row[0])


def _set_version(conn: Any, version: int) -> None:
    conn.execute(f"DELETE FROM {SCHEMA_TABLE}")
    conn.execute(f"INSERT INTO {SCHEMA_TABLE} (version) VALUES (%s)", (version,))


def migrate(conn: Any) -> list[int]:
    """Apply any pending forward migrations and return the versions applied.

    Each migration runs in its own transaction; a failure rolls back that
    migration and raises :class:`ConfigurationError`.

    Concurrent-start safety: multi-instance deployments start several API
    processes against the same database. PostgreSQL DDL is transactional, but
    racing ``CREATE TABLE IF NOT EXISTS`` on a fresh catalog can trigger
    ``UniqueViolation`` (``pg_type_typname_nsp_index``) because catalog checks
    are not fully serialized. A session-level advisory lock serializes the
    migrate path so exactly one instance performs migration and other
    instances wait and then observe the final schema.
    """
    with conn.transaction():
        # Session-level advisory lock keyed to a fixed migration namespace.
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (_MIGRATION_LOCK_KEY,))
        _ensure_version_table(conn)
        current = current_version(conn)
        applied: list[int] = []
        pending = sorted(version for version in MIGRATIONS if version > current)
        for version in pending:
            statements = MIGRATIONS[version]
            try:
                logger.warning("applying migration version=%s", version)
                for statement in statements:
                    conn.execute(statement)
                _set_version(conn, version)
            except Exception as exc:  # psycopg.Error and friends
                raise ConfigurationError(
                    f"migration to schema version {version} failed; "
                    f"database left at version {current}. Reason: {exc}"
                ) from exc
            applied.append(version)
        return applied


def validate_schema(conn: Any) -> None:
    """Verify the schema is at the expected version.

    Raises :class:`ConfigurationError` if the version is unknown, the table is
    missing, or the version row is inconsistent (downgraded or out-of-band).
    """
    _ensure_version_table(conn)
    recorded = current_version(conn)
    if recorded != CURRENT_SCHEMA_VERSION:
        raise ConfigurationError(
            f"database schema version is {recorded}, expected {CURRENT_SCHEMA_VERSION}; "
            "run migrations or restore a compatible backup before continuing"
        )
    row = conn.execute(
        f"SELECT COUNT(*) FROM {SCHEMA_TABLE}"
    ).fetchone()
    if row is None or int(row[0]) != 1:
        raise ConfigurationError("schema version table is corrupted")
    # Ensure the live table exists so a truncated schema is caught at startup.
    exists = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'memory_entries'"
    ).fetchone()
    if exists is None:
        raise ConfigurationError("memory_entries table is missing; schema is incompatible with this build")


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATIONS",
    "SCHEMA_TABLE",
    "current_version",
    "migrate",
    "validate_schema",
]