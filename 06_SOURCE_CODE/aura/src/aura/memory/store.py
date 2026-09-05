"""Memory storage.

The store is a plain, injectable persistence contract. Engines pass one in via
dependency injection; memory is never a hidden global mutable dictionary.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from aura.foundation.errors import NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryEntry, MemoryType


@runtime_checkable
class MemoryStore(Protocol):
    def add(self, entry: MemoryEntry) -> MemoryEntry: ...

    def get(self, memory_id: MemoryId) -> MemoryEntry: ...

    def delete(self, memory_id: MemoryId) -> None: ...

    def search(
        self,
        *,
        text: str = "",
        kind: MemoryType | None = None,
        tags: tuple[str, ...] = (),
    ) -> list[MemoryEntry]: ...

    def all(self) -> Iterator[MemoryEntry]: ...

    def count(self) -> int: ...


@dataclass
class InMemoryMemoryStore:
    """Default in-memory store. Not thread-shared by default; wrap externally if needed."""

    _entries: dict[str, MemoryEntry]

    def __init__(self) -> None:
        object.__setattr__(self, "_entries", {})

    def add(self, entry: MemoryEntry) -> MemoryEntry:
        self._entries[str(entry.id)] = entry
        return entry

    def get(self, memory_id: MemoryId) -> MemoryEntry:
        if str(memory_id) not in self._entries:
            raise NotFoundError(f"memory entry not found: {memory_id}")
        return self._entries[str(memory_id)]

    def delete(self, memory_id: MemoryId) -> None:
        self._entries.pop(str(memory_id), None)

    def search(
        self,
        *,
        text: str = "",
        kind: MemoryType | None = None,
        tags: tuple[str, ...] = (),
    ) -> list[MemoryEntry]:
        needle = text.strip().lower()
        results = []
        for entry in self._entries.values():
            if kind is not None and entry.kind is not kind:
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


__all__ = ["InMemoryMemoryStore", "MemoryStore"]