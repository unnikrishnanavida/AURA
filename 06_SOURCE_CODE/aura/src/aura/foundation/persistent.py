"""Minimal durable JSON store (Phase 2A).

A small, dependency-free SQLite-backed key/value store used to make canonical
state durable across process restarts (automation tasks, learning lineage,
knowledge claims). It deliberately avoids introducing an ORM or a second
"database architecture": it mirrors the existing stdlib ``sqlite3`` pattern
already used by :mod:`aura.memory.sqlite_store`, and exposes only the tiny
surface the engines need (``put`` / ``get`` / ``delete`` / ``load_all``).

Thread safety: a process-wide lock serialises writes and each operation uses
its own short-lived connection, which is the safe cross-thread usage of
``sqlite3``. WAL is enabled so concurrent readers do not block a writer.

This is data infrastructure (an ordinary persistence helper), not a new
architectural subsystem; it does not create a second task/memory/learning
engine.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

_JSON_TYPES = (str, int, float, bool)  # scalars we pass through as-is


class SQLiteJsonStore:
    """Thread-safe SQLite-backed JSON key/value store.

    Keys are arbitrary strings; values are JSON-serialisable Python objects.
    Migrations are a schema-version row that callers can read; engines that
    need structured migration use the version to decide how to interpret rows.
    """

    def __init__(self, path: str | Path, *, table: str = "kv") -> None:
        self.path = str(path)
        self.table = table
        self._lock = threading.RLock()
        parent = Path(self.path).parent
        if str(parent):
            parent.mkdir(parents=True, exist_ok=True)
        self._migrate_schema()

    # -- connection / schema -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _migrate_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} ("
                "k TEXT PRIMARY KEY, v TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _meta ("
                "k TEXT PRIMARY KEY, v TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO _meta (k, v) VALUES ('schema_version', '1')"
            )
            conn.commit()

    @property
    def schema_version(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT v FROM _meta WHERE k='schema_version'").fetchone()
        return int(row[0]) if row else 1

    # -- core API -------------------------------------------------------------

    def put(self, key: str, value: Any) -> None:
        payload = value if isinstance(value, _JSON_TYPES) else json.dumps(value, default=str)
        with self._lock, self._connect() as conn:
            conn.execute(
                f"INSERT INTO {self.table} (k, v, updated_at) VALUES (?, ?, ?) "
                f"ON CONFLICT(k) DO UPDATE SET v=excluded.v, updated_at=excluded.updated_at",
                (key, payload, _now()),
            )
            conn.commit()

    def get(self, key: str) -> Any:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                f"SELECT v FROM {self.table} WHERE k=?", (key,)
            ).fetchone()
        return self._decode(row[0]) if row else None

    def delete(self, key: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(f"DELETE FROM {self.table} WHERE k=?", (key,))
            conn.commit()

    def load_all(self) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(f"SELECT k, v FROM {self.table}").fetchall()
        return {k: self._decode(v) for k, v in rows}

    def __contains__(self, key: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                f"SELECT 1 FROM {self.table} WHERE k=?", (key,)
            ).fetchone()
        return row is not None

    def __len__(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        """Close is advisory: each op already uses its own short-lived connection."""

    @staticmethod
    def _decode(raw: str) -> Any:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


__all__ = ["SQLiteJsonStore"]