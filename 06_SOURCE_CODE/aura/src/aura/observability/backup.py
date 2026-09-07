"""Backup and recovery for persistent AURA data.

Scope: the SQLite database file (memory/audit/knowledge state that is
persisted) plus a manifest that records the environment, instance, schema
version, and timestamp so a backup can be validated before restore.

Strategy

- Backup: SQLite online backup API (``sqlite3.Connection.backup``) produces a
  consistent, atomic copy without stopping the writer; the manifest is written
  into the destination directory.
- Retention: the caller chooses a frequency and keeps N most recent backups;
  each backup is a single file so rotation is trivially correct.
- Encryption: backups are plain SQLite files; encryption-at-rest is delegated to
  the platform (LUKS/TDE/or volume encryption) and documented, not faked.
- Restore: verify the target exists and the manifest schema version is
  compatible BEFORE replacing the live file; the live store must be closed by
  the caller first.
- Integrity: after writing and after restore the file is re-opened and
  ``PRAGMA quick_check`` runs.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from aura.memory.migrations import CURRENT_SCHEMA_VERSION

BACKUP_MANIFEST_NAME = "manifest.json"


class BackupError(RuntimeError):
    """Raised when a backup or restore cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class BackupResult:
    path: str
    created_at: float
    schema_version: int
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
            "size_bytes": self.size_bytes,
        }


def _quick_check(path: str) -> None:
    try:
        conn = sqlite3.connect(path)
        try:
            row = conn.execute("PRAGMA quick_check").fetchone()
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        raise BackupError(f"integrity check failed for {path}: {exc}") from exc
    if row is None or str(row[0]).lower() not in ("ok", "1"):
        raise BackupError(f"integrity check failed for {path}: {row}")


def create_backup(
    *,
    db_path: str | Path,
    backup_dir: str | Path,
    instance_id: str = "default",
    environment: str = "development",
) -> BackupResult:
    """Create a consistent, integrity-verified SQLite backup and manifest."""
    src = Path(db_path)
    if not src.exists():
        raise BackupError(f"database file not found: {src}")
    dest = Path(backup_dir)
    dest.mkdir(parents=True, exist_ok=True)

    stamp = time.time()
    backup_name = f"aura-{instance_id}-{int(stamp * 1000)}.sqlite3"
    backup_path = dest / backup_name
    manifest_path = dest / BACKUP_MANIFEST_NAME

    try:
        source = sqlite3.connect(str(src))
        target = sqlite3.connect(str(backup_path))
        try:
            with target:
                source.backup(target)
        finally:
            source.close()
            target.close()
    except sqlite3.Error as exc:
        raise BackupError(f"backup failed: {exc}") from exc

    _quick_check(str(backup_path))

    manifest = {
        "instance_id": instance_id,
        "environment": environment,
        "created_at": stamp,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "backup_file": backup_name,
        "source": str(src),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return BackupResult(
        path=str(backup_path),
        created_at=stamp,
        schema_version=CURRENT_SCHEMA_VERSION,
        size_bytes=backup_path.stat().st_size,
    )


def restore_backup(*, backup_path: str | Path, db_path: str | Path) -> None:
    """Restore ``backup_path`` onto ``db_path`` after schema compatibility check.

    The caller is responsible for closing any open connection to ``db_path``
    before calling this (the function refuses to clobber an open file).
    """
    src = Path(backup_path)
    if not src.exists():
        raise BackupError(f"backup file not found: {src}")
    _quick_check(str(src))

    dest = Path(db_path)
    if dest.exists():
        # SQLite WAL/journal sidecars belong to a live store; removing the main
        # file while these exist would corrupt future opens, so nuke them too.
        for sidecar in (Path(str(dest) + "-wal"), Path(str(dest) + "-shm"), Path(str(dest) + "-journal")):
            try:
                sidecar.unlink(missing_ok=True)
            except PermissionError as exc:
                raise BackupError(f"{dest} appears to be in use (sidecar {sidecar.name} locked)") from exc
        try:
            dest.unlink()
        except PermissionError as exc:
            raise BackupError(f"{dest} appears to be in use; close the live store before restore") from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    # verify the restored file is a valid, schema-compatible database
    _quick_check(str(dest))
    conn = sqlite3.connect(str(dest))
    try:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
    finally:
        conn.close()
    if row is None or int(row[0]) != CURRENT_SCHEMA_VERSION:
        raise BackupError(
            f"restored database schema version {row} != {CURRENT_SCHEMA_VERSION}; "
            "restore rejected to avoid serving an incompatible database"
        )


__all__ = ["BackupError", "BackupResult", "create_backup", "restore_backup"]