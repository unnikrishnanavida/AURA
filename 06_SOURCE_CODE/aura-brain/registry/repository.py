"""In-memory repository implementation for registry entries."""

from __future__ import annotations

from .exceptions import RegistryConflictError, RegistryNotFoundError
from .interfaces import RegistryStore
from .models import RegistryEntry


class InMemoryRegistryRepository(RegistryStore[RegistryEntry]):
    """Simple dictionary-backed repository for registry entries."""

    def __init__(self) -> None:
        self._entries: dict[str, RegistryEntry] = {}

    def save(self, item: RegistryEntry) -> None:
        if item.name in self._entries:
            raise RegistryConflictError(f"Entry '{item.name}' already exists.")
        self._entries[item.name] = item

    def load(self, name: str) -> RegistryEntry:
        try:
            return self._entries[name]
        except KeyError as exc:
            raise RegistryNotFoundError(f"Entry '{name}' was not found.") from exc

    def delete(self, name: str) -> None:
        if name not in self._entries:
            raise RegistryNotFoundError(f"Entry '{name}' was not found.")
        del self._entries[name]

    def all(self) -> list[RegistryEntry]:
        return list(self._entries.values())

    def update(self, item: RegistryEntry) -> None:
        """Update an existing entry."""
        self._entries[item.name] = item

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()


class SqliteRegistryRepository(RegistryStore[RegistryEntry]):
    """SQLite-backed registry repository with simple transactional semantics.

    This implementation stores `RegistryEntry` objects as JSON blobs and
    provides atomic save/update/delete operations within SQLite transactions.
    """

    def __init__(self, path: str = ":memory:") -> None:
        import sqlite3
        import json
        from dataclasses import asdict

        self._path = path
        self._sqlite = sqlite3.connect(self._path, check_same_thread=False)
        # Ensure we store metadata and payload as JSON text
        self._sqlite.execute(
            """CREATE TABLE IF NOT EXISTS registry (
            name TEXT PRIMARY KEY,
            kind TEXT,
            metadata TEXT,
            payload TEXT
        )"""
        )
        self._sqlite.commit()
        self._json = json
        self._asdict = asdict

    def _row_to_entry(self, row: tuple) -> RegistryEntry:
        name, kind, metadata_json, payload = row
        data = self._json.loads(payload)
        metadata = self._json.loads(metadata_json) if metadata_json else {}
        return RegistryEntry.from_dict({"name": name, "kind": kind, "data": data, "metadata": metadata})

    def save(self, item: RegistryEntry) -> None:
        cur = self._sqlite.cursor()
        try:
            cur.execute("BEGIN")
            cur.execute(
                "INSERT INTO registry (name, kind, metadata, payload) VALUES (?, ?, ?, ?)",
                (item.name, item.kind, self._json.dumps(self._asdict(item.metadata)), self._json.dumps(item.data)),
            )
            self._sqlite.commit()
        except Exception as exc:
            self._sqlite.rollback()
            raise RegistryConflictError(str(exc)) from exc

    def load(self, name: str) -> RegistryEntry:
        cur = self._sqlite.execute("SELECT name, kind, metadata, payload FROM registry WHERE name = ?", (name,))
        row = cur.fetchone()
        if row is None:
            raise RegistryNotFoundError(f"Entry '{name}' was not found.")
        return self._row_to_entry(row)

    def delete(self, name: str) -> None:
        cur = self._sqlite.cursor()
        try:
            cur.execute("BEGIN")
            cur.execute("DELETE FROM registry WHERE name = ?", (name,))
            if cur.rowcount == 0:
                raise RegistryNotFoundError(f"Entry '{name}' was not found.")
            self._sqlite.commit()
        except Exception:
            self._sqlite.rollback()
            raise

    def all(self) -> list[RegistryEntry]:
        cur = self._sqlite.execute("SELECT name, kind, metadata, payload FROM registry")
        return [self._row_to_entry(row) for row in cur.fetchall()]

    def update(self, item: RegistryEntry) -> None:
        cur = self._sqlite.cursor()
        try:
            cur.execute("BEGIN")
            cur.execute(
                "UPDATE registry SET kind = ?, metadata = ?, payload = ? WHERE name = ?",
                (item.kind, self._json.dumps(self._asdict(item.metadata)), self._json.dumps(item.data), item.name),
            )
            if cur.rowcount == 0:
                raise RegistryNotFoundError(f"Entry '{item.name}' was not found.")
            self._sqlite.commit()
        except Exception:
            self._sqlite.rollback()
            raise

    def clear(self) -> None:
        cur = self._sqlite.cursor()
        cur.execute("DELETE FROM registry")
        self._sqlite.commit()
