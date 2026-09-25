"""Audit spool unit tests (local JSON-lines durability; no database)."""

from __future__ import annotations

from pathlib import Path

from aura.security.spool import SPOOL_FILENAME, AuditSpool


def _record(event_id: str, *, action: str = "test.deny") -> dict[str, object]:
    return {
        "event_id": event_id,
        "action": action,
        "actor": "alice",
        "resource": "api",
        "decision": "deny",
        "reason": "unit test",
        "timestamp": "2026-09-25T10:00:00+00:00",
        "correlation_id": None,
        "payload": {"n": 1},
    }


def test_spool_appends_and_reads_in_order(tmp_path: Path) -> None:
    spool = AuditSpool(tmp_path)
    spool.append(_record("ev-1"))
    spool.append(_record("ev-2", action="test.allow"))
    records = spool.entries()
    assert [r["event_id"] for r in records] == ["ev-1", "ev-2"]
    assert [r["action"] for r in records] == ["test.deny", "test.allow"]
    assert spool.count() == 2
    assert (tmp_path / SPOOL_FILENAME).exists()


def test_spool_survives_reopen(tmp_path: Path) -> None:
    AuditSpool(tmp_path).append(_record("ev-durable"))
    reopened = AuditSpool(tmp_path)
    assert reopened.count() == 1
    assert reopened.entries()[0]["event_id"] == "ev-durable"


def test_spool_remove_is_atomic(tmp_path: Path) -> None:
    spool = AuditSpool(tmp_path)
    for event_id in ("ev-1", "ev-2", "ev-3"):
        spool.append(_record(event_id))
    assert spool.remove({"ev-2"}) == 1
    assert [r["event_id"] for r in spool.entries()] == ["ev-1", "ev-3"]
    # Removing already-absent ids is a no-op.
    assert spool.remove({"ev-2"}) == 0
    assert spool.count() == 2


def test_spool_clear_drops_all(tmp_path: Path) -> None:
    spool = AuditSpool(tmp_path)
    spool.append(_record("ev-1"))
    spool.append(_record("ev-2"))
    assert spool.clear() == 2
    assert spool.count() == 0
    assert not spool.path.exists()


def test_spool_skips_torn_line_without_blocking_replay(tmp_path: Path) -> None:
    spool = AuditSpool(tmp_path)
    spool.append(_record("ev-ok"))
    # Simulate a crash that truncated a write mid-line.
    with spool.path.open("a", encoding="utf-8") as handle:
        handle.write('{"event_id": "ev-torn", "action": "test"')
        handle.write("\n")
    records = spool.entries()
    assert [r["event_id"] for r in records] == ["ev-ok"]
    assert spool.count() == 1