"""Migration utilities for aura-memory."""

from __future__ import annotations

import dataclasses
import hashlib
import sqlite3
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union


@dataclasses.dataclass(frozen=True)
class Migration:
    id: str
    description: str
    script: Union[str, Callable[[sqlite3.Connection], None]]

    def checksum(self) -> str:
        payload = self.id + self.description + (self.script if isinstance(self.script, str) else "")
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class MigrationManager:
    def __init__(self, db_path: str, table: str = "schema_migrations") -> None:
        self.db_path = db_path
        self.table = table
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self.table} (id TEXT PRIMARY KEY, description TEXT, checksum TEXT, applied_at REAL)"
        )
        self._conn.commit()

    def applied_ids(self) -> List[str]:
        cursor = self._conn.execute(f"SELECT id FROM {self.table} ORDER BY applied_at")
        return [row[0] for row in cursor.fetchall()]

    def apply(self, migrations: Iterable[Migration]) -> None:
        applied = set(self.applied_ids())
        for migration in migrations:
            if migration.id in applied:
                continue
            self._execute(migration)

    def _execute(self, migration: Migration) -> None:
        if isinstance(migration.script, str):
            self._conn.executescript(migration.script)
        else:
            migration.script(self._conn)
        self._conn.execute(
            f"INSERT INTO {self.table} (id, description, checksum, applied_at) VALUES (?, ?, ?, strftime('%s','now'))",
            (migration.id, migration.description, migration.checksum()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def load_migrations_from_directory(directory: str) -> List[Migration]:
    directory_path = Path(directory)
    migrations: List[Migration] = []
    for path in sorted(directory_path.glob("*.sql")):
        migrations.append(
            Migration(
                id=path.stem,
                description=path.name,
                script=path.read_text(encoding="utf-8"),
            )
        )
    return migrations


__all__ = ["Migration", "MigrationManager", "load_migrations_from_directory"]
