"""Offline-first sync queue for desktop/mobile clients.

A small, durable, idempotent operation queue:

- operations are JSON records with an ``idempotency_key`` (client-generated
  from the logical request) so re-queuing a retry never duplicates the effect;
- enqueue is append-only JSONL (flushed); a torn final line from a crash is
  skipped;
- :meth:`replay` feeds records to an *executor* callable — records that the
  executor reports as done are removed; exhausted records (attempt budget)
  are surfaced as failures and dropped only after explicit reporting;
- conflict handling is last-write-wins by ``sequence`` (a genuine, documented
  strategy — not silently ignored).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

SPOOL_NAME = "offline_ops.jsonl"
MAX_ATTEMPTS = 3


class OfflineQueue:
    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._path = self._directory / SPOOL_NAME
        self._sequence = 0

    # -- enqueue ------------------------------------------------------------

    def enqueue(self, *, op: str, params: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Add one operation (deduplicated by idempotency_key)."""
        now = self._sequence
        record = {
            "op": op,
            "params": params,
            "idempotency_key": idempotency_key,
            "sequence": now,
            "attempts": 0,
        }
        existing = self._by_key().get(idempotency_key)
        if existing is not None:
            # Same logical request re-sent -> bump sequence (LWW), keep once.
            self._rewrite_dropping([existing])
            record["sequence"] = existing["sequence"] + 1
        self._sequence += 1
        self._append(record)
        return record

    def pending(self) -> list[dict[str, Any]]:
        return self._read()

    def count(self) -> int:
        return len(self.pending())

    # -- replay ---------------------------------------------------------------

    def replay(
        self,
        executor: Callable[[dict[str, Any]], bool],
        *,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> dict[str, int]:
        """Feed pending records to ``executor``; returns {replayed, failed, remaining}.

        A record whose executor returns True is done and removed; otherwise its
        attempt counter is incremented. Records exceeding ``max_attempts`` are
        removed and reported as ``failed`` (never silently swallowed).
        """
        pending = self.pending()
        done: set[int] = set()
        dropped: list[dict[str, Any]] = []
        bumped = False
        failures = 0
        for record in pending:
            try:
                ok = bool(executor(record))
            except Exception:  # noqa: BLE001 - executor failure == record failure
                ok = False
            if ok:
                done.add(record["sequence"])
            else:
                bumped = True
                record["attempts"] = int(record.get("attempts", 0)) + 1
                if record["attempts"] >= max_attempts:
                    dropped.append(record)
                    failures += 1
        # Persist: drop done + exhausted records; keep the rest with new attempts.
        keep = [
            r
            for r in pending
            if r["sequence"] not in done and all(r["sequence"] != d["sequence"] for d in dropped)
        ]
        if done or dropped or bumped:
            self._rewrite_to(keep)
        return {
            "replayed": len(done),
            "failed": failures,
            "remaining": len(keep),
        }

    # -- internals -------------------------------------------------------------

    def _path_file(self) -> Path:
        return self._path

    def _append(self, record: dict[str, Any]) -> None:
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()

    def _read(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as source:
            for line in source:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # torn crash line
        return sorted(records, key=lambda r: int(r.get("sequence", 0)))

    def _by_key(self) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for record in self._read():
            lookup[record.get("idempotency_key", "")] = record
        return lookup

    def _rewrite_dropping(self, drop: list[dict[str, Any]]) -> None:
        drop_ids = {r["sequence"] for r in drop}
        keep = [r for r in self._read() if r["sequence"] not in drop_ids]
        self._rewrite_to(keep)

    def _rewrite_to(self, records: list[dict[str, Any]]) -> None:
        import tempfile

        fd, tmp = tempfile.mkstemp(dir=str(self._directory), prefix="queue.", suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, sort_keys=True) + "\n")
            import os

            os.replace(tmp, self._path)
        except BaseException:
            import os

            with __import__("contextlib").suppress(OSError):
                os.unlink(tmp)
            raise

    def clear(self) -> int:
        count = self.count()
        self._path.unlink(missing_ok=True)
        return count


__all__ = ["OfflineQueue"]