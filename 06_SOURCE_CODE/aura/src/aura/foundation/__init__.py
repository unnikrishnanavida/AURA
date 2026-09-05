"""AURA foundation.

The single authoritative set of cross-cutting primitives shared by every
engine: identifiers, correlation/execution/request ids, domain errors, result
types, status enums, clocks, deterministic random sources, validation,
serialization, and lifecycle primitives.
"""

from __future__ import annotations

from aura.foundation.cancellation import CancellationToken, CancellationTokenSource
from aura.foundation.clock import Clock, FrozenClock, ManualClock, SystemClock
from aura.foundation.errors import (
    ApprovalRequiredError,
    AuraError,
    AuraTimeoutError,
    BudgetExhaustedError,
    CancelledError,
    CapabilityError,
    ConfigurationError,
    InvalidStateTransitionError,
    LifecycleError,
    LoopDetectedError,
    NotFoundError,
    PermissionDeniedError,
    RecoveryError,
    SafetyDeniedError,
    ToolExecutionError,
    ValidationError,
)
from aura.foundation.ids import (
    AgentId,
    ClaimId,
    CorrelationId,
    EventId,
    ExecutionId,
    GoalId,
    MemoryId,
    PlanId,
    RequestId,
    ToolCallId,
    new_hex,
)
from aura.foundation.lifecycle import Component, LifecycleGuard, LifecycleState
from aura.foundation.random_source import RandomSource, SecureRandom, SeededRandom
from aura.foundation.result import Failure, Result, Status, Success, err, ok
from aura.foundation.serialization import json_dumps, to_jsonable
from aura.foundation.validation import ensure, validators

__all__ = [
    "AgentId",
    "ApprovalRequiredError",
    "AuraError",
    "AuraTimeoutError",
    "BudgetExhaustedError",
    "CancelledError",
    "CancellationToken",
    "CancellationTokenSource",
    "CapabilityError",
    "ClaimId",
    "Clock",
    "Component",
    "ConfigurationError",
    "CorrelationId",
    "EventId",
    "ExecutionId",
    "Failure",
    "FrozenClock",
    "GoalId",
    "InvalidStateTransitionError",
    "LifecycleError",
    "LifecycleGuard",
    "LifecycleState",
    "LoopDetectedError",
    "ManualClock",
    "MemoryId",
    "NotFoundError",
    "PermissionDeniedError",
    "PlanId",
    "RandomSource",
    "RecoveryError",
    "RequestId",
    "Result",
    "SafetyDeniedError",
    "SecureRandom",
    "SeededRandom",
    "Status",
    "Success",
    "SystemClock",
    "ToolCallId",
    "ToolExecutionError",
    "ValidationError",
    "err",
    "ensure",
    "json_dumps",
    "new_hex",
    "ok",
    "to_jsonable",
    "validators",
]