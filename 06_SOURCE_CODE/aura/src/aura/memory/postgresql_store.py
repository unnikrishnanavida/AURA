"""PostgreSQL-ready store interface.

PostgreSQL is NOT a mandatory dependency: the interface documents how a PG
backend must behave and what row format it must persist, and the in-process
runtime never requires a PG driver. A production deployment that wants
PostgreSQL implements this protocol (or the :class:`MemoryStore` protocol)
against the same row format produced by :mod:`aura.memory.serialization`.

Current status: interface-only. The reference persistent store is
:class:`aura.memory.sqlite_store.SQLiteMemoryStore`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol, runtime_checkable

from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryEntry, MemoryStatus, MemoryType


@runtime_checkable
class PostgreSQLMemoryStore(Protocol):
    """Contract for a PostgreSQL-backed memory store (no driver bundled)."""

    def add(self, entry: MemoryEntry) -> MemoryEntry: ...

    def get(self, memory_id: MemoryId) -> MemoryEntry: ...

    def update(self, entry: MemoryEntry) -> MemoryEntry: ...

    def delete(self, memory_id: MemoryId) -> None: ...

    def search(
        self,
        *,
        text: str = "",
        kind: MemoryType | None = None,
        tags: tuple[str, ...] = (),
        status: MemoryStatus | None = None,
    ) -> list[MemoryEntry]: ...

    def all(self) -> Iterator[MemoryEntry]: ...

    def count(self) -> int: ...

    def archive(self, entry: MemoryEntry) -> None: ...

    def restore(self, memory_id: MemoryId) -> MemoryEntry: ...

    @contextmanager
    def transaction(self) -> Iterator[None]: ...


__all__ = ["PostgreSQLMemoryStore"]