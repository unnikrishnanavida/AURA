"""Observability tests: flight recorder, replay, provenance, metrics."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aura.foundation.clock import FrozenClock
from aura.foundation.errors import NotFoundError
from aura.foundation.ids import CorrelationId, ExecutionId
from aura.observability.flight_recorder import InMemoryFlightRecorder
from aura.observability.metrics import Metrics
from aura.observability.replay import STATE_MARKER, ReplayEngine


def make_recorder() -> tuple[InMemoryFlightRecorder, ExecutionId]:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=UTC))
    recorder = InMemoryFlightRecorder(clock=clock)
    execution = ExecutionId.new()
    recorder.record(
        event_type="observation.recorded",
        source="test",
        execution_id=execution,
        correlation_id=CorrelationId.new(),
        payload={"question": "q"},
    )
    recorder.record(
        event_type="decision",
        source="test",
        execution_id=execution,
        correlation_id=CorrelationId.new(),
        payload={"answer": "yes"},
    )
    return recorder, execution


def test_flight_recorder_records_events() -> None:
    recorder, execution = make_recorder()
    events = recorder.events(execution_id=execution)
    assert len(events) == 2
    assert events[0].event_type == "observation.recorded"
    assert events[0].sequence == 1
    assert events[1].sequence == 2


def test_event_has_all_fields() -> None:
    recorder, execution = make_recorder()
    event = recorder.events(execution_id=execution)[0]
    data = event.to_dict()
    assert set(data) >= {"event_id", "execution_id", "correlation_id", "timestamp", "source", "event_type", "sequence"}


def test_replay_orders_and_flags_states() -> None:
    recorder, execution = make_recorder()
    recorder.record(
        event_type=STATE_MARKER,
        source="test",
        execution_id=execution,
        correlation_id=CorrelationId.new(),
        payload={"state": {"x": 1}, "origin": "RECORDED"},
    )
    replay = ReplayEngine(recorder).trajectory(execution)
    assert replay.reconstructable
    assert replay.trajectory()[0].sequence == 1
    assert replay.states
    assert replay.states[0].origin == "RECORDED"


def test_replay_missing_execution_raises() -> None:
    recorder = InMemoryFlightRecorder()
    with pytest.raises(NotFoundError):
        ReplayEngine(recorder).trajectory(ExecutionId.new())


def test_replay_state_at() -> None:
    recorder, execution = make_recorder()
    recorder.record(
        event_type=STATE_MARKER,
        source="test",
        execution_id=execution,
        correlation_id=CorrelationId.new(),
        payload={"state": {"x": 1}, "origin": "RECORDED"},
    )
    engine = ReplayEngine(recorder)
    assert engine.state_at(execution, 2) is None  # marker recorded at sequence 3
    assert engine.state_at(execution, 3) is not None


def test_provenance_graph_explains_chain() -> None:
    recorder, execution = make_recorder()
    events = recorder.events(execution_id=execution)
    events[1].payload.setdefault("caused_by", [str(events[0].event_id)])  # type: ignore[attr-defined]
    graph = ReplayEngine(recorder).graph(execution)
    explanation = graph.explain(str(events[1].event_id))
    assert explanation["target"] == str(events[1].event_id)
    assert len(explanation["cause_chain"]) == 2


def test_metrics_increment_and_snapshot() -> None:
    metrics = Metrics()
    metrics.increment("executions", amount=3)
    metrics.increment("successes")
    assert metrics.count("executions") == 3
    snapshot = metrics.snapshot()
    assert snapshot["counters"]["executions"] == 3
    assert snapshot["counters"]["successes"] == 1


def test_metrics_timed() -> None:
    metrics = Metrics()
    with metrics.timed("query"):
        pass
    assert metrics.snapshot()["latency"]["query"]["count"] == 1