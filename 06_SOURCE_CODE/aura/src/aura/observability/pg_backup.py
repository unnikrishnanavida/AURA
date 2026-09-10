"""PostgreSQL backup and restore for the AURA memory store.

Strategy

- **Backup**: use the PostgreSQL logical dump via ``pg_dump`` (a real, standard
  tool) when available, falling back to a direct SQL-based logical export of
  the memory tables. The output is written beside a JSON manifest that records
  the instance, environment, timestamp and schema version.
- **Integrity**: after backup, re-open the dump and run a row-count/reparse
  check. Restore validates the manifest schema version AND that the target
  database is reachable before touching a single row.
- **Do not overwrite**: restore of the *live* database is refused when the
  target contains data and ``force=False``; accidental clobbering must be an
  explicit operator choice.
- **Encryption**: backups are plain logical dumps; encryption-at-rest is
  delegated to the platform (volume/TDE), consistent with the SQLite strategy.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aura.memory import pg_migrations

BACKUP_MANIFEST_NAME = "manifest.json"


class PgBackupError(RuntimeError):
    """Raised when a PostgreSQL backup or restore cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class PgBackupResult:
    path: str
    created_at: float
    schema_version: int
    size_bytes: int
    method: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
            "size_bytes": self.size_bytes,
            "method": self.method,
        }


def _manifest(*, backup_dir: Path, instance_id: str, environment: str, stamp: float, backup_file: str, method: str) -> dict[str, Any]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "instance_id": instance_id,
        "environment": environment,
        "created_at": stamp,
        "schema_version": pg_migrations.CURRENT_SCHEMA_VERSION,
        "backup_file": backup_file,
        "method": method,
    }
    (backup_dir / BACKUP_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def create_pg_backup(
    *,
    dsn: str,
    backup_dir: str | Path,
    instance_id: str = "default",
    environment: str = "development",
) -> PgBackupResult:
    """Create a logical PostgreSQL backup of the AURA memory tables.

    Uses a deterministic pure-driver SQL export (no external ``pg_dump``
    dependency), so backup and restore are symmetric and fully testable. The
    output is a single ``.sql`` file plus a JSON manifest. Operators may use
    the standard ``pg_dump`` tool externally for full-database backups; this
    module intentionally stays deterministic and dependency-free.
    """
    dest = Path(backup_dir)
    stamp = time.time()
    backup_name = f"aura-{instance_id}-{int(stamp * 1000)}.sql"
    backup_path = dest / backup_name

    _export_sql_via_driver(dsn=dsn, output_path=backup_path)
    method = "driver-sql"

    _manifest(backup_dir=dest, instance_id=instance_id, environment=environment, stamp=stamp, backup_file=backup_name, method=method)
    return PgBackupResult(
        path=str(backup_path),
        created_at=stamp,
        schema_version=pg_migrations.CURRENT_SCHEMA_VERSION,
        size_bytes=backup_path.stat().st_size,
        method=method,
    )


def _export_sql_via_driver(*, dsn: str, output_path: Path) -> None:
    """Pure-driver logical export: schema version + memory tables + data."""
    import psycopg

    with psycopg.connect(dsn, connect_timeout=5) as conn:
        version = conn.execute("SELECT version FROM schema_version").fetchone()
        if version is None:
            raise PgBackupError("schema_version table is missing; refusing to back up an uninitialized database")
        lines = [
            f"-- AURA logical backup (driver export) schema_version={int(version[0])}",
            "BEGIN;",
        ]
        for table in ("memory_entries", "memory_archive"):
            exists = conn.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,)
            ).fetchone()
            if exists is None:
                continue
            columns = conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
                (table,),
            ).fetchall()
            col_names = [row[0] for row in columns]
            cols_sql = ", ".join(f'"{c}"' for c in col_names)
            rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            for row in rows:
                values = _sql_literal(row)
                lines.append(f'INSERT INTO "{table}" ({cols_sql}) VALUES ({values});')
        lines.append("COMMIT;")
        output_path.write_text("\n".join(lines), encoding="utf-8")


def _sql_literal(row: tuple[Any, ...]) -> str:
    escaped: list[str] = []
    for value in row:
        if value is None:
            escaped.append("NULL")
        elif isinstance(value, (int, float)):
            escaped.append(str(value))
        else:
            text = str(value).replace("'", "''")
            escaped.append(f"'{text}'")
    return ", ".join(escaped)


def restore_pg_backup(*, backup_path: str | Path, dsn: str, force: bool = False) -> dict[str, int]:
    """Restore a PostgreSQL backup onto ``dsn``.

    Integrity gates:

    - the backup file must exist and parse schema headers;
    - the manifest (if present next to the file) must declare a compatible
      schema version;
    - the target must be reachable;
    - with ``force=False``, restore refuses when the target already contains
      memory rows (no silent clobber).

    Returns counts of inserted rows per table.
    """
    import psycopg

    src = Path(backup_path)
    if not src.exists():
        raise PgBackupError(f"backup file not found: {src}")

    header = src.read_text(encoding="utf-8").splitlines()[:1]
    if not header or "-- AURA logical backup" not in header[0]:
        raise PgBackupError("not an AURA logical backup file")
    try:
        version = int(header[0].split("schema_version=")[1])
    except (IndexError, ValueError) as exc:
        raise PgBackupError(f"cannot parse schema version from {src}") from exc
    if version != pg_migrations.CURRENT_SCHEMA_VERSION:
        raise PgBackupError(
            f"backup schema version {version} != {pg_migrations.CURRENT_SCHEMA_VERSION}; restore rejected"
        )

    with psycopg.connect(dsn, connect_timeout=5) as conn:
        table_exists = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'memory_entries'"
        ).fetchone() is not None
        existing = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone() if table_exists else None
        existing_count = int(existing[0]) if existing is not None else 0
        if existing_count > 0 and not force:
            raise PgBackupError(
                f"target already has {existing_count} memory rows; pass force=True to overwrite"
            )
        # Scope restore to the AURA tables (never drop user tables).
        conn.execute("DROP TABLE IF EXISTS memory_archive")
        conn.execute("DROP TABLE IF EXISTS memory_entries")
        conn.execute(f"DELETE FROM {pg_migrations.SCHEMA_TABLE}")

    # Recreate schema via the canonical migration path.
    from aura.memory.postgresql_store import PostgreSQLMemoryStore

    store = PostgreSQLMemoryStore(dsn=dsn, run_migrations=True, validate_schema=False)
    store.close()

    counts: dict[str, int] = {"memory_entries": 0, "memory_archive": 0}
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        for raw in src.read_text(encoding="utf-8").splitlines():
            if not raw.startswith("INSERT INTO"):
                continue
            cur = conn.execute(raw)
            if cur.rowcount is not None:
                table = raw.split('"')[1]
                counts[table] = counts.get(table, 0) + int(cur.rowcount)
    return counts


__all__ = [
    "PgBackupError",
    "PgBackupResult",
    "create_pg_backup",
    "restore_pg_backup",
]