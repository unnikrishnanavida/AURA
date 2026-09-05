"""SQLite-backed memory store.

Production-capable implementation of the :class:`MemoryStore` contract using
the standard-library SQLite driver:

- WAL journaling (concurrent readers, single writer), 30s busy timeout;
- one guarded connection (``check_same_thread=False`` + re-entrant lock)
  serializes writes — correct and adequate for this local-first runtime;
- forward migrations are applied on open and validated;
- `PRAGMA quick_check` detects physical corruption on open when configured;
- :meth:`transaction` gives atomicity for operations that span multiple
  statements (e.g. versioned correction, archive moves).

PostgreSQL is supported via the same protocol/row format; no driver is bundled
so PostgreSQL never becomes a mandatory local dependency.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aura.foundation.errors import NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory import migrations
from aura.memory.models import MemoryEntry, MemoryStatus, MemoryType
from aura.memory.serialization import entry_to_row, row_to_entry


def _live_column_names() -> tuple[str, ...]:
    sample = entry_to_row(MemoryEntry(id=MemoryId.new(), key="", kind=MemoryType.SEMANTIC, content={}))
    names = [name for name in sample if name != "schema_version"]
    return tuple(names)


_LIVE_COLUMNS = _live_column_names()
_ARCHIVE_COLUMNS = _live_column_names() + ("archived_at",)


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(count))


class StorageIntegrityError(RuntimeError):
    """Raised when the on-disk database fails an integrity check."""


class SQLiteMemoryStore:
    """File-backed, transactional, migrated memory store."""

    def __init__(
        self,
        *,
        path: str | Path = "data/aura.sqlite3",
        run_migrations: bool = True,
        integrity_check: bool = True,
        clock: Any = None,
    ) -> None:
        object.__setattr__(self, "_path", Path(path))
        self._path: Path
        if str(self._path) != ":memory:":
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._clock = clock
        self._conn = sqlite3.connect(
            str(self._path),
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        if integrity_check:
            self._verify_integrity()
        if run_migrations:
            with self._lock:
                migrations.migrate(self._conn)
            migrations.validate_schema(self._conn)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _verify_integrity(self) -> None:
        try:
            row = self._conn.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError as exc:
            raise StorageIntegrityError(f"database file is corrupt on open: {exc}") from exc
        if row is None or str(row[0]).lower() not in ("ok", "1"):
            raise StorageIntegrityError(f"database integrity check failed: {row}")

    # -- protocol ------------------------------------------------------------
    def add(self, entry: MemoryEntry) -> MemoryEntry:
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        with self._lock, self.transaction():
            self._conn.execute(
                f"INSERT OR REPLACE INTO memory_entries ({', '.join(cols)}) "
                f"VALUES ({_placeholders(len(cols))})",
                [row[c] for c in cols],
            )
        return entry

    def get(self, memory_id: MemoryId) -> MemoryEntry:
        with self._lock:
            raw = self._conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries WHERE id = ?",
                (str(memory_id),),
            ).fetchone()
        if raw is None:
            raise NotFoundError(f"memory entry not found: {memory_id}")
        return _entry_from_rows(raw)

    def update(self, entry: MemoryEntry) -> MemoryEntry:
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        sets = ", ".join(f"{c} = ?" for c in cols if c != "id")
        values = [row[c] for c in cols if c != "id"] + [str(entry.id)]
        with self._lock, self.transaction():
            self._conn.execute(f"UPDATE memory_entries SET {sets} WHERE id = ?", values)
        return entry

    def delete(self, memory_id: MemoryId) -> None:
        with self._lock, self.transaction():
            self._conn.execute("DELETE FROM memory_entries WHERE id = ?", (str(memory_id),))

    def search(
        self,
        *,
        text: str = "",
        kind: MemoryType | None = None,
        tags: tuple[str, ...] = (),
        status: MemoryStatus | None = None,
    ) -> list[MemoryEntry]:
        needle = text.strip().lower()
        clauses: list[str] = []
        params: list[Any] = []
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind.value)
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        if needle:
            clauses.append("(key LIKE ? OR content LIKE ?)")
            like = f"%{needle}%"
            params.extend([like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries {where}", params
            ).fetchall()

        results: list[MemoryEntry] = []
        for raw in rows:
            entry = _entry_from_rows(raw)
            if tags and not set(tags).issubset(set(entry.tags)):
                continue
            if needle:
                haystack = f"{entry.key} {entry.content}".lower()
                if needle not in haystack:
                    continue
            results.append(entry)
        return results

    def all(self) -> Iterator[MemoryEntry]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries"
            ).fetchall()
        for raw in rows:
            yield _entry_from_rows(raw)

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()
        return int(row[0]) if row else 0

    def archive(self, entry: MemoryEntry) -> None:
        entry.status = MemoryStatus.ARCHIVED
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        archived_at = self._now_iso()
        with self._lock, self.transaction():
            self._conn.execute("DELETE FROM memory_entries WHERE id = ?", (str(entry.id),))
            self._conn.execute(
                f"INSERT INTO memory_archive ({', '.join(cols)}, archived_at) "
                f"VALUES ({_placeholders(len(cols) + 1)})",
                [row[c] for c in cols] + [archived_at],
            )

    def restore(self, memory_id: MemoryId) -> MemoryEntry:
        with self._lock, self.transaction():
            raw = self._conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)}, archived_at "
                f"FROM memory_archive WHERE id = ?",
                (str(memory_id),),
            ).fetchone()
            if raw is None:
                raise NotFoundError(f"archived memory entry not found: {memory_id}")
            self._conn.execute("DELETE FROM memory_archive WHERE id = ?", (str(memory_id),))
        entry = _entry_from_archive_row(raw)
        entry.status = MemoryStatus.ACTIVE
        self.add(entry)
        return entry

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError:
                # already inside a transaction on this connection
                yield
                return
            try:
                yield
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise

    def _now_iso(self) -> str:
        if self._clock is not None and hasattr(self._clock, "utcnow_iso"):
            stamped = self._clock.utcnow_iso()
            if isinstance(stamped, str):
                return stamped
        return datetime.now(UTC).isoformat()


def _entry_from_rows(raw: tuple[Any, ...]) -> MemoryEntry:
    mapping = {name: value for name, value in zip(_LIVE_COLUMNS, raw, strict=True)}
    return row_to_entry(mapping)


def _entry_from_archive_row(raw: tuple[Any, ...]) -> MemoryEntry:
    mapping = {name: value for name, value in zip(_ARCHIVE_COLUMNS, raw, strict=True)}
    return row_to_entry(mapping)


__all__ = ["SQLiteMemoryStore", "StorageIntegrityError"]