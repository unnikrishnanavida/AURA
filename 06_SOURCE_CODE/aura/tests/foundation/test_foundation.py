"""Foundation unit tests: ids, errors, results, clocks, validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aura.foundation.clock import FrozenClock, ManualClock, SystemClock
from aura.foundation.errors import (
    AuraError,
    CapabilityError,
    ConfigurationError,
    NotFoundError,
    ValidationError,
)
from aura.foundation.ids import (
    ClaimId,
    CorrelationId,
    ExecutionId,
    GoalId,
    MemoryId,
    PlanId,
    new_hex,
)
from aura.foundation.result import Failure, Result, Success, err, ok
from aura.foundation.validation import ensure, validators


def test_new_hex_length() -> None:
    assert len(new_hex()) == 16
    assert len(new_hex(4)) == 8


def test_ids_unique() -> None:
    ids = {
        ExecutionId.new(),
        CorrelationId.new(),
        ExecutionId.new(),  # distinct value but same class
        MemoryId.new(),
        ClaimId.new(),
        GoalId.new(),
        PlanId.new(),
    }
    assert len(ids) == 7
    classes = {type(i) for i in ids}
    assert len(classes) == 6


def test_id_round_trip() -> None:
    eid = ExecutionId.new()
    assert ExecutionId.from_str(str(eid)) == eid
    assert ExecutionId.from_str(eid) == eid


def test_id_str_prefix() -> None:
    assert str(ExecutionId.new()).startswith("ex-")
    assert str(CorrelationId.new()).startswith("co-")


def test_ok_result() -> None:
    result: Result[int] = ok(42)
    assert result.is_ok
    assert not result.is_err
    assert result.unwrap() == 42
    assert isinstance(result, Success)


def test_err_result() -> None:
    result: Result[int] = err(CapabilityError("no"))
    assert not result.is_ok
    assert isinstance(result, Failure)
    with pytest.raises(CapabilityError):
        result.unwrap()


def test_result_map() -> None:
    result: Result[int] = ok(4).map(lambda n: n * 2)
    assert result.unwrap() == 8


def test_frozen_clock() -> None:
    now = datetime(2024, 1, 1, tzinfo=UTC)
    clock = FrozenClock(now)
    assert clock.now() == now
    assert clock.utcnow_iso() == now.isoformat()


def test_manual_clock_advance() -> None:
    clock = ManualClock()
    start = clock.now()
    clock.advance(5.0)
    assert (clock.now() - start).total_seconds() == 5.0


def test_system_clock() -> None:
    clock = SystemClock()
    assert clock.now() is not None
    assert clock.utcnow_iso()


def test_error_hierarchy() -> None:
    assert isinstance(CapabilityError("x"), AuraError)
    assert isinstance(ConfigurationError("x"), AuraError)
    assert isinstance(NotFoundError("x"), AuraError)
    assert isinstance(ValidationError("x"), AuraError)


def test_aura_error_fields() -> None:
    error = CapabilityError("no capability")
    assert error.message == "no capability"
    assert error.code == "capability.missing"
    assert error.to_dict() == {"code": "capability.missing", "message": "no capability"}


def test_validators_identifier() -> None:
    assert validators.identifier("safe_name32") == "safe_name32"
    with pytest.raises(ValidationError):
        validators.identifier("not valid!")


def test_validators_in_range() -> None:
    assert validators.in_range(0.5, 0.0, 1.0) == 0.5
    with pytest.raises(ValidationError):
        validators.in_range(2.0, 0.0, 1.0)


def test_ensure() -> None:
    ensure(True, "ok")
    with pytest.raises(ValidationError):
        ensure(False, "must hold")