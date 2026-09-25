"""Durable-audit failure-path unit tests (simulated store; no live PostgreSQL)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aura.api.distributed import PostgreSQLAuditLog
from aura.foundation.ids import EventId
from aura.security.audit import coerce_event_id


class _Cursor:
    """psycopg-like cursor backed by a fixed row list."""

    def __init__(self, rows: list[object]) -> None:
        self._rows = list(rows)
        self._index = 0

    def fetchone(self) -> object:
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def fetchall(self) -> list[object]:
        rows = list(self._rows)
        self._rows = []
        return rows


class _Connection:
    """Fake psycopg connection: records SQL, raises when the store is "down"."""

    def __init__(self, state: _State) -> None:
        self._state = state

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def transaction(self) -> _Connection:
        return self

    def execute(self, sql: str, params: tuple[object, ...] | None = None) -> _Cursor:
        self._state.sql_log.append((sql, tuple(params) if params is not None else ()))
        if self._state.fail:
            raise RuntimeError("simulated unreachable store")
        upper = sql.strip().upper()
        if upper.startswith("SELECT 1 FROM INFORMATION_SCHEMA"):
            return _Cursor(list(self._state.information_rows))
        if upper.startswith("SELECT COUNT("):
            return _Cursor(list(self._state.count_rows))
        if upper.startswith("SELECT EVENT_ID,") or (upper.startswith("SELECT ") and "FROM AURA_AUDIT_EVENTS" in upper):
            return _Cursor(list(self._state.select_rows))
        if "RETURNING" in upper:
            return _Cursor(list(self._state.returning_rows))
        return _Cursor([])


class _State:
    """Simulated shared audit store with scriptable health."""

    def __init__(self) -> None:
        self.fail = False
        self.sql_log: list[tuple[str, tuple[object, ...]]] = []
        self.information_rows: list[object] = []
        self.count_rows: list[object] = []
        self.select_rows: list[object] = []
        self.returning_rows: list[object] = []

    def connection(self) -> _Connection:
        return _Connection(self)

    @property
    def last_sql(self) -> str:
        return self.sql_log[-1][0]

    def insert_params(self) -> tuple[object, ...]:
        for sql, params in reversed(self.sql_log):
            if sql.strip().upper().startswith("INSERT INTO AURA_AUDIT_EVENTS"):
                return params
        return ()


@pytest.fixture
def state() -> _State:
    return _State()


@pytest.fixture
def log(state: _State, tmp_path: Path) -> PostgreSQLAuditLog:
    return PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))  # type: ignore[arg-type]


def test_record_insert_is_idempotent_and_carries_event_id(log: PostgreSQLAuditLog, state: _State) -> None:
    entry = log.record(
        action="perm.deny",
        actor="alice",
        resource="api",
        decision="deny",
        reason="policy",
        event_id="ev-explicit-001",
        correlation_id="co-abc",
    )
    params = state.insert_params()
    assert len(params) == 9
    assert params[0] == "ev-explicit-001"
    assert params[1] == "perm.deny"
    assert "ON CONFLICT (event_id) DO NOTHING" in state.last_sql
    assert "EVENT_ID" in state.last_sql.upper()
    assert str(entry.event_id) == "ev-explicit-001"


def test_record_generates_event_id_when_not_supplied(log: PostgreSQLAuditLog, state: _State) -> None:
    entry = log.record(action="x", actor="sys", resource="api", decision="allow", reason="r")
    assert entry.event_id is not None
    assert state.insert_params()[0] == str(entry.event_id)
    parsed = EventId.from_str(str(entry.event_id))
    assert str(parsed) == str(entry.event_id)


def test_unreachable_store_spools_and_buffers(log: PostgreSQLAuditLog, state: _State) -> None:
    state.fail = True
    entry = log.record(
        action="rate_limit.deny",
        actor="10.0.0.9",
        resource="api",
        decision="deny",
        reason="store down",
        event_id="ev-spool-1",
    )
    assert any(r.action == "rate_limit.deny" for r in log.entries())
    assert log._spool.count() == 1  # noqa: SLF001 - white-box durability check
    assert log._spool.entries()[0]["event_id"] == "ev-spool-1"  # noqa: SLF001
    assert str(entry.event_id) == "ev-spool-1"
def test_replay_spooled_resyncs_and_clears(log: PostgreSQLAuditLog, state: _State) -> None:
    state.fail = True
    for i in range(3):
        log.record(action=f"a.{i}", actor="bob", resource="api", decision="deny", reason="down", event_id=f"ev-q-{i}")
    assert log._spool.count() == 3  # noqa: SLF001

    # Store recovers; resync drains the spool idempotently.
    state.fail = False
    state.returning_rows = [("ev-q-0",)]  # fresh cursor per INSERT -> all "inserted"
    result = log.replay_spooled()
    assert result == {"replayed": 3, "skipped": 0, "remaining": 0}
    assert log._spool.count() == 0  # noqa: SLF001
    assert log.replay_spooled() == {"replayed": 0, "skipped": 0, "remaining": 0}


def test_replay_spooled_keeps_spool_while_store_still_down(log: PostgreSQLAuditLog, state: _State) -> None:
    state.fail = True
    log.record(action="x", actor="sys", resource="api", decision="allow", reason="down", event_id="ev-keep-1")
    result = log.replay_spooled()
    assert result == {"replayed": 0, "skipped": 0, "remaining": 1}
    assert log._spool.count() == 1  # noqa: SLF001


def test_replay_spooled_skips_records_already_present(log: PostgreSQLAuditLog, state: _State) -> None:
    state.fail = True
    log.record(action="x", actor="sys", resource="api", decision="allow", reason="down", event_id="ev-dup-1")
    state.fail = False
    state.returning_rows = []  # every INSERT conflicts -> already persisted
    result = log.replay_spooled()
    assert result == {"replayed": 0, "skipped": 1, "remaining": 0}
    assert log._spool.count() == 0  # noqa: SLF001


def test_entries_filters_build_parameterized_where(log: PostgreSQLAuditLog, state: _State) -> None:
    state.select_rows = [("ev-1", "a.1", "alice", "api", "deny", "r", "2026-09-25T10:00:00+00:00", "co-1", "{}")]
    got = log.entries(actor="alice", decision="deny", limit=5)
    assert len(got) == 1
    assert got[0].action == "a.1"
    sql, params = state.sql_log[-1]
    assert "WHERE actor = %s AND decision = %s" in sql
    assert "LIMIT %s" in sql
    assert params == ("alice", "deny", 5)
    assert str(got[0].event_id) == "ev-1"


def test_entries_maps_row_event_id_and_payload(log: PostgreSQLAuditLog, state: _State) -> None:
    state.select_rows = [
        ("ev-payload-1", "x", "sys", "api", "allow", "reason", "2026-09-25T10:00:00+00:00", None, '{"k": 1}')
    ]
    got = log.entries()
    assert str(got[0].event_id) == "ev-payload-1"
    assert got[0].payload == {"k": 1}
    assert got[0].correlation_id is None


def test_entries_serves_local_truth_when_store_down(log: PostgreSQLAuditLog, state: _State) -> None:
    state.fail = True
    log.record(
        action="z",
        actor="carol",
        resource="api",
        decision="deny",
        reason="down",
        event_id="ev-loc",
        correlation_id="co-local",
    )
    got = log.entries(actor="carol")
    assert len(got) == 1
    assert got[0].action == "z"
    assert got[0].correlation_id == "co-local"
    assert log.entries(actor="nobody-else") == []


def test_count_uses_db_and_falls_back_locally(log: PostgreSQLAuditLog, state: _State) -> None:
    state.count_rows = [(7,)]
    assert log.count() == 7
    state.fail = True
    assert log.count() == 0
    log.record(action="y", actor="dave", resource="api", decision="allow", reason="down")
    assert log.count() == 1  # buffer + spool hold the same record (deduped)


def test_coerce_event_id_parses_prefixed_and_plain() -> None:
    assert str(coerce_event_id(None)).startswith("ev-")
    assert str(coerce_event_id("ev-custom-1")) == "ev-custom-1"
    assert str(coerce_event_id("custom-2")) == "ev-custom-2"