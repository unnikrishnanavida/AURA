"""Database migrations for the persistent memory store.

Forward-only, versioned schema management:

- a ``schema_version`` table records the applied version as a single row;
- migrations are a deterministic ordered list; each runs inside one
  transaction and bumps the version on success;
- opening a store calls :func:`migrate`, which validates the current version,
  applies any pending migrations, and raises on failure — a failed migration
  leaves the previous version intact (the transaction is rolled back) so the
  operator can decide; it is never silently re-applied or skipped.

Rollback of an *already applied* migration is performed by restoring the
previous database file/backup (see the backup strategy) rather than by
synthetic down-migrations — this keeps forward migrations simple and safe.
"""

from __future__ import annotations

import sqlite3

from aura.foundation.errors import ConfigurationError

SCHEMA_TABLE = "schema_version"
INITIAL_VERSION = 0
CURRENT_SCHEMA_VERSION = 2

_COLUMNS_SQL = """
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL,
    confidence_fact REAL NOT NULL,
    confidence_source REAL NOT NULL,
    confidence_freshness REAL NOT NULL,
    confidence_relevance REAL NOT NULL,
    provenance_source TEXT NOT NULL,
    provenance_execution_id TEXT,
    provenance_creator TEXT NOT NULL,
    provenance_details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_access TEXT NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',
    expires_at TEXT,
    links TEXT NOT NULL DEFAULT '{}',
    sensitivity TEXT NOT NULL,
    status TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    supersedes TEXT,
    observed_at TEXT,
    retention_ttl_seconds REAL,
    retention_max_versions INTEGER,
    schema_version INTEGER NOT NULL DEFAULT 1
"""

# Migration 1: initial schema for live entries and the archive table.
MIGRATION_1_STATEMENTS: tuple[str, ...] = (
    f"CREATE TABLE IF NOT EXISTS memory_entries ({_COLUMNS_SQL})",
    "CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key)",
    "CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory_entries(kind)",
    "CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_entries(status)",
    "CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at)",
    (
        "CREATE TABLE IF NOT EXISTS memory_archive ("
        f"{_COLUMNS_SQL},"
        " archived_at TEXT NOT NULL"
        ")"
    ),
)

# Migration 2: add the optional retrieval-isolation scope (MEM-1). `scope` is
# an optional TEXT column; existing rows are unscoped (NULL) which keeps them
# readable and backward compatible.
MIGRATION_2_STATEMENTS: tuple[str, ...] = (
    "ALTER TABLE memory_entries ADD COLUMN scope TEXT",
    "ALTER TABLE memory_archive ADD COLUMN scope TEXT",
    "CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_entries(scope)",
)

MIGRATIONS: dict[int, tuple[str, ...]] = {
    1: MIGRATION_1_STATEMENTS,
    2: MIGRATION_2_STATEMENTS,
}


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_TABLE} (version INTEGER NOT NULL)"
    )


def current_version(conn: sqlite3.Connection) -> int:
    """Return the recorded schema version (0 on a fresh database)."""
    _ensure_version_table(conn)
    row = conn.execute(f"SELECT version FROM {SCHEMA_TABLE}").fetchone()
    if row is None:
        return INITIAL_VERSION
    return int(row[0])


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"DELETE FROM {SCHEMA_TABLE}")
    conn.execute(f"INSERT INTO {SCHEMA_TABLE} (version) VALUES (?)", (version,))


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Apply any pending forward migrations and return the versions applied.

    Each migration runs in its own transaction; a failure rolls back that
    migration and raises :class:`ConfigurationError`.
    """
    _ensure_version_table(conn)
    current = current_version(conn)
    applied: list[int] = []
    pending = sorted(version for version in MIGRATIONS if version > current)
    for version in pending:
        statements = MIGRATIONS[version]
        try:
            conn.execute("BEGIN IMMEDIATE")
            for statement in statements:
                conn.execute(statement)
            _set_version(conn, version)
            conn.execute("COMMIT")
        except sqlite3.Error as exc:
            conn.execute("ROLLBACK")
            raise ConfigurationError(
                f"migration to schema version {version} failed; "
                f"database left at version {current}. Reason: {exc}"
            ) from exc
        applied.append(version)
    return applied


def validate_schema(conn: sqlite3.Connection) -> None:
    """Verify the schema is at the expected version and internally consistent.

    Raises :class:`ConfigurationError` if the version is unknown or the version
    table is inconsistent (downgraded or out-of-band writes).
    """
    recorded = current_version(conn)
    if recorded != CURRENT_SCHEMA_VERSION:
        raise ConfigurationError(
            f"database schema version is {recorded}, expected {CURRENT_SCHEMA_VERSION}; "
            "run migrations or restore a compatible backup before continuing"
        )
    rows = conn.execute(
        f"SELECT COUNT(*) FROM {SCHEMA_TABLE}"
    ).fetchone()
    if rows is None or rows[0] != 1:
        raise ConfigurationError("schema version table is corrupted")


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATIONS",
    "SCHEMA_TABLE",
    "current_version",
    "migrate",
    "validate_schema",
]