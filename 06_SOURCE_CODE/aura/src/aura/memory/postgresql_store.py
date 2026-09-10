"""PostgreSQL-backed memory store.

Real implementation of the :class:`aura.memory.store.MemoryStore` contract on
PostgreSQL using psycopg3 + psycopg-pool.

Design:

- The driver is an *optional* dependency (``pip install aura[postgresql]``).
  Importing this module raises :class:`ConfigurationError` when psycopg is not
  installed, and the factory never silently falls back to another backend.
- A connection pool bounds live connections; every operation borrows a
  connection for the duration of the statement (or transaction).
- Schema is managed by :mod:`aura.memory.pg_migrations` (versioned, forward,
  transactional, fails-closed on incompatible/missing schema).
- Writes that need atomicity (correction, archive move, restore) run inside a
  real transaction; a failure rolls back and re-raises.
- Connection/authentication failures raise immediately with an explicit
  message — PostgreSQL must never degrade quietly to another backend.

The row format is identical to SQLite so all three stores share the same
:class:`MemoryEntry` semantics (identity, provenance, confidence axes,
sensitivity, retention, timestamps, version, lineage, lifecycle status,
relationships, archival state).
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from typing import Any

from aura.foundation.errors import ConfigurationError, NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory import pg_migrations
from aura.memory.models import MemoryEntry, MemoryStatus, MemoryType
from aura.memory.serialization import entry_to_row, row_to_entry


def _optional_driver() -> Any:
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "psycopg is not installed; run `pip install aura[postgresql]` "
            "to use the PostgreSQL memory backend"
        ) from exc
    return psycopg


def _optional_pool() -> Any:
    try:
        import psycopg_pool
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "psycopg-pool is not installed; run `pip install aura[postgresql]` "
            "to use the PostgreSQL memory backend"
        ) from exc
    return psycopg_pool


def _live_column_names() -> tuple[str, ...]:
    sample = entry_to_row(MemoryEntry(id=MemoryId.new(), key="", kind=MemoryType.SEMANTIC, content={}))
    return tuple(name for name in sample if name != "schema_version")


def _row_tuple(raw: Any) -> tuple[Any, ...]:
    """psycopg3 rows are tuples already; normalize Record objects defensively."""
    return tuple(raw)


def _entry_from_rows(raw: tuple[Any, ...]) -> MemoryEntry:
    mapping = {name: value for name, value in zip(_LIVE_COLUMNS, raw, strict=True)}
    return row_to_entry(mapping)


_LIVE_COLUMNS = _live_column_names()
_ARCHIVE_COLUMNS = _LIVE_COLUMNS + ("archived_at",)
class PostgreSQLMemoryStore:
    """Durable, transactional, migrated memory store backed by PostgreSQL."""

    def __init__(
        self,
        *,
        dsn: str | None,
        min_connections: int = 1,
        max_connections: int = 5,
        run_migrations: bool = True,
        validate_schema: bool = True,
        clock: Any = None,
    ) -> None:
        if not dsn:
            raise ConfigurationError(
                "postgresql backend requires storage.postgresql_dsn; "
                "refusing to fall back to another backend"
            )
        self._dsn = dsn
        self._lock = threading.RLock()
        self._clock = clock
        self._local = threading.local()
        _optional_driver()  # fail fast if the optional driver is missing
        pool_lib = _optional_pool()

        try:
            self._pool = pool_lib.ConnectionPool(
                conninfo=self._dsn,
                min_size=min_connections,
                max_size=max_connections,
                open=True,
                timeout=min(10, max(2, min_connections * 3)),
                kwargs={"connect_timeout": 5},
            )
        except Exception as exc:  # incl. psycopg.OperationalError
            raise ConfigurationError(
                f"failed to connect PostgreSQL memory store: {exc}"
            ) from exc

        # Probe the pool immediately so a down/refusing/unreachable server is an
        # explicit startup failure instead of surfacing seconds later as a
        # mid-request error. No degrade-to-another-backend path exists.
        try:
            with self._conn() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # incl. psycopg_pool.PoolTimeout
            self._pool.close()
            raise ConfigurationError(
                f"failed to connect PostgreSQL memory store: {exc}"
            ) from exc

        if run_migrations:
            try:
                with self._conn() as conn:
                    pg_migrations.migrate(conn)
            except Exception:
                self._pool.close()
                raise
        if validate_schema:
            try:
                with self._conn() as conn:
                    pg_migrations.validate_schema(conn)
            except Exception:
                self._pool.close()
                raise

    def close(self) -> None:
        pool = getattr(self, "_pool", None)
        if pool is not None:
            pool.close()

    # -- protocol ----------------------------------------------------------

    def add(self, entry: MemoryEntry) -> MemoryEntry:
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        sql = (
            f"INSERT INTO memory_entries ({', '.join(cols)}) "
            f"VALUES ({', '.join('%s' for _ in cols)}) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"{', '.join(f'{c} = EXCLUDED.{c}' for c in cols if c != 'id')}"
        )
        with self._conn() as conn:
            conn.execute(sql, [row[c] for c in cols])
        return entry

    def get(self, memory_id: MemoryId) -> MemoryEntry:
        with self._conn() as conn:
            raw = conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries WHERE id = %s",
                (str(memory_id),),
            ).fetchone()
        if raw is None:
            raise NotFoundError(f"memory entry not found: {memory_id}")
        return _entry_from_rows(_row_tuple(raw))

    def update(self, entry: MemoryEntry) -> MemoryEntry:
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        sets = ", ".join(f"{c} = %s" for c in cols if c != "id")
        values = [row[c] for c in cols if c != "id"] + [str(entry.id)]
        with self._conn() as conn:
            conn.execute(f"UPDATE memory_entries SET {sets} WHERE id = %s", values)
        return entry

    def delete(self, memory_id: MemoryId) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM memory_entries WHERE id = %s", (str(memory_id),))

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
            clauses.append("kind = %s")
            params.append(kind.value)
        if status is not None:
            clauses.append("status = %s")
            params.append(status.value)
        if needle:
            clauses.append("(key ILIKE %s OR content ILIKE %s)")
            like = f"%{needle}%"
            params.extend([like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._conn() as conn:
            raws = conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries {where}", params
            ).fetchall()

        results: list[MemoryEntry] = []
        for raw in raws:
            entry = _entry_from_rows(_row_tuple(raw))
            if tags and not set(tags).issubset(set(entry.tags)):
                continue
            if needle:
                haystack = f"{entry.key} {entry.content}".lower()
                if needle not in haystack:
                    continue
            results.append(entry)
        return results

    def all(self) -> Iterator[MemoryEntry]:
        with self._conn() as conn:
            raws = conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)} FROM memory_entries"
            ).fetchall()
        for raw in raws:
            yield _entry_from_rows(_row_tuple(raw))

    def count(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()
        return int(row[0]) if row is not None else 0

    def archive(self, entry: MemoryEntry) -> None:
        entry.status = MemoryStatus.ARCHIVED
        row = entry_to_row(entry)
        cols = list(_LIVE_COLUMNS)
        archived_at = self._now_iso()
        with self.transaction(), self._conn() as conn:
            conn.execute("DELETE FROM memory_entries WHERE id = %s", (str(entry.id),))
            conn.execute(
                f"INSERT INTO memory_archive ({', '.join(cols)}, archived_at) "
                f"VALUES ({', '.join('%s' for _ in cols + ['archived_at'])})",
                [row[c] for c in cols] + [archived_at],
            )

    def restore(self, memory_id: MemoryId) -> MemoryEntry:
        with self.transaction(), self._conn() as conn:
            raw = conn.execute(
                f"SELECT {', '.join(_LIVE_COLUMNS)}, archived_at "
                f"FROM memory_archive WHERE id = %s",
                (str(memory_id),),
            ).fetchone()
            if raw is None:
                raise NotFoundError(f"archived memory entry not found: {memory_id}")
            conn.execute("DELETE FROM memory_archive WHERE id = %s", (str(memory_id),))
        entry = _entry_from_rows(_row_tuple(raw[:-1]))
        entry.status = MemoryStatus.ACTIVE
        self.add(entry)
        return entry

    # -- transaction support ----------------------------------------------

    @contextmanager
    def _conn(self) -> Iterator[Any]:
        """Borrow a connection, preferring the thread-local active transaction.

        Operations called inside a :meth:`transaction` on the same thread share
        that transaction's pinned connection so they participate in the same
        atomic unit; otherwise each borrows a fresh pooled connection.
        """
        txn = getattr(self._local, "txn_conn", None)
        if txn is not None:
            yield txn
            return
        with self._pool.connection() as conn:
            yield conn

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Run a real database transaction.

        Nested calls on the same thread reuse the outer transaction instead of
        opening a second one. A failure rolls back; connection is pinned
        thread-locally for the duration so inner operations stay atomic.
        """
        if getattr(self._local, "txn_conn", None) is not None:
            yield
            return
        with self._conn() as conn:
            self._local.txn_conn = conn
            try:
                conn.execute("BEGIN")
                yield
                conn.execute("COMMIT")
            except BaseException:
                with suppress(Exception):
                    conn.execute("ROLLBACK")
                raise
            finally:
                self._local.txn_conn = None

    def _now_iso(self) -> str:
        if self._clock is not None and hasattr(self._clock, "utcnow_iso"):
            stamped = self._clock.utcnow_iso()
            if isinstance(stamped, str):
                return stamped
        return datetime.now(UTC).isoformat()


__all__ = ["PostgreSQLMemoryStore"]