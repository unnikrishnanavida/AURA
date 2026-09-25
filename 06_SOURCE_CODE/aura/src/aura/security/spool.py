"""Durable audit spool.

When the shared PostgreSQL audit store is unreachable,
:class:`aura.api.distributed.PostgreSQLAuditLog` keeps decisions observable in
the process (bounded in-memory buffer) **and** writes each record to a local
JSON-lines spool file so it survives process restarts. Once the store is
reachable again :meth:`PostgreSQLAuditLog.replay_spooled` resyncs the spool
into PostgreSQL idempotently (same ``event_id`` is a no-op).

Design:

- Append-only JSON-lines in ``spool.jsonl``; every append is flushed.
- :meth:`remove` rewrites the file atomically (temp file + ``os.replace``) and
  is only invoked by the successful-resync path, so a crash mid-rewrite never
  corrupts the spool.
- A torn final line from a crash during an outage is skipped (the record is
  already lost; one bad line must not block replay of the rest).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SPOOL_FILENAME = "spool.jsonl"


class AuditSpool:
    """Local JSON-lines spool of audit records awaiting durable storage."""

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._directory / SPOOL_FILENAME

    def append(self, record: dict[str, Any]) -> None:
        """Append one record (JSON object) to the spool, flushed to disk."""
        line = json.dumps(record, sort_keys=True, default=str) + "\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()

    def entries(self) -> list[dict[str, Any]]:
        """Return all spooled records in append order."""
        path = self.path
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # Torn append from a crash during an outage: skip the line,
                    # never block replay of the remaining records.
                    continue
        return records

    def count(self) -> int:
        return len(self.entries())

    def remove(self, event_ids: set[str]) -> int:
        """Atomically drop the given event ids from the spool.

        Rewrites the spool to a temp file and ``os.replace``s it into place;
        returns the number of records removed. A crash never leaves a partial
        spool because the original file is untouched until the replace.
        """
        records = self.entries()
        if not records:
            return 0
        kept = [r for r in records if str(r.get("event_id")) not in event_ids]
        removed = len(records) - len(kept)
        if removed == 0:
            return 0
        if not kept:
            self.path.unlink(missing_ok=True)
            return removed
        fd, tmp_name = tempfile.mkstemp(dir=str(self._directory), prefix="spool.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for record in kept:
                    handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
                    handle.flush()
            os.replace(tmp_name, self.path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise
        return removed

    def clear(self) -> int:
        """Remove the spool file entirely; return the number of records dropped."""
        count = self.count()
        self.path.unlink(missing_ok=True)
        return count


__all__ = ["AuditSpool", "SPOOL_FILENAME"]