"""Memory storage.

The store is a plain, injectable persistence contract. Engines pass one in via
dependency injection; memory is never a hidden global mutable dictionary.

The contract is backend-agnostic: any implementation that can persist the row
format produced by :mod:`aura.memory.serialization` and satisfy the protocol
below can serve as a live store. Reference implementations are
:class:`InMemoryMemoryStore` (development) and
:class:`aura.memory.sqlite_store.SQLiteMemoryStore` (file-backed persistence).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from aura.foundation.errors import NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryEntry, MemoryStatus, MemoryType


@runtime_checkable
class MemoryStore(Protocol):
    """Persistence contract every memory backend must satisfy."""

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
        scope: str | None = None,
    ) -> list[MemoryEntry]: ...

    def all(self) -> Iterator[MemoryEntry]: ...

    def count(self) -> int: ...

    def archive(self, entry: MemoryEntry) -> None: ...

    def restore(self, memory_id: MemoryId) -> MemoryEntry: ...

    @contextmanager
    def transaction(self) -> Iterator[None]: ...


@dataclass
class InMemoryMemoryStore:
    """Default in-memory store. Not thread-shared by default; wrap externally if needed."""

    _entries: dict[str, MemoryEntry] = field(default_factory=dict, init=False, repr=False)
    _archived: dict[str, MemoryEntry] = field(default_factory=dict, init=False, repr=False)

    def __init__(self) -> None:
        object.__setattr__(self, "_entries", {})
        object.__setattr__(self, "_archived", {})

    def add(self, entry: MemoryEntry) -> MemoryEntry:
        self._entries[str(entry.id)] = entry
        return entry

    def get(self, memory_id: MemoryId) -> MemoryEntry:
        if str(memory_id) not in self._entries:
            raise NotFoundError(f"memory entry not found: {memory_id}")
        return self._entries[str(memory_id)]

    def update(self, entry: MemoryEntry) -> MemoryEntry:
        return self.add(entry)

    def delete(self, memory_id: MemoryId) -> None:
        self._entries.pop(str(memory_id), None)

    def search(
        self,
        *,
        text: str = "",
        kind: MemoryType | None = None,
        tags: tuple[str, ...] = (),
        status: MemoryStatus | None = None,
        scope: str | None = None,
    ) -> list[MemoryEntry]:
        needle = text.strip().lower()
        results = []
        for entry in self._entries.values():
            if kind is not None and entry.kind is not kind:
                continue
            if status is not None and entry.status is not status:
                continue
            if scope is not None and entry.scope != scope:
                continue
            if tags and not set(tags).issubset(set(entry.tags)):
                continue
            if needle:
                haystack = f"{entry.key} {entry.content}".lower()
                if needle not in haystack:
                    continue
            results.append(entry)
        return results

    def all(self) -> Iterator[MemoryEntry]:
        yield from self._entries.values()

    def count(self) -> int:
        return len(self._entries)

    def archive(self, entry: MemoryEntry) -> None:
        entry.status = MemoryStatus.ARCHIVED
        self._entries.pop(str(entry.id), None)
        self._archived[str(entry.id)] = entry

    def restore(self, memory_id: MemoryId) -> MemoryEntry:
        entry = self._archived.pop(str(memory_id), None)
        if entry is None:
            raise NotFoundError(f"archived memory entry not found: {memory_id}")
        entry.status = MemoryStatus.ACTIVE
        self._entries[str(entry.id)] = entry
        return entry

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield


__all__ = ["InMemoryMemoryStore", "MemoryStore"]