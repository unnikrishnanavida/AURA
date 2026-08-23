"""Goal domain models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import AgentId, GoalId

__all__ = [
    "GoalStatus",
    "GoalPriority",
    "GoalConstraint",
    "SuccessCriterion",
    "Goal",
]


class GoalStatus(enum.Enum):
    """Lifecycle of a goal."""

    CREATED = "created"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        return self in {
            GoalStatus.COMPLETED,
            GoalStatus.PARTIAL,
            GoalStatus.FAILED,
            GoalStatus.CANCELLED,
        }


class GoalPriority(enum.IntEnum):
    """Priority ordering; higher value runs first."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class GoalConstraint:
    """A hard constraint on a goal.

    ``field`` is a dotted world-state path (e.g. ``filesystem.file_created``),
    ``allowed`` is the set of permitted values (or a single value).
    """

    field: str
    allowed: frozenset[Any] = frozenset()
    reason: str = ""

    def permits(self, value: Any) -> bool:
        if not self.allowed:
            return True
        return value in self.allowed


@dataclass(frozen=True)
class SuccessCriterion:
    """A declarative, checkable success criterion.

    ``condition`` supports a small deterministic predicate language:
    ``path.to.field == value``, ``path.to.field != value``,
    ``path.to.field exists``. This keeps evaluation free of arbitrary code.
    """

    condition: str

    def evaluate(self, world_state: dict[str, Any]) -> bool:
        """Evaluate the criterion against a flat state mapping."""
        return _evaluate_condition(self.condition, world_state)


def _evaluate_condition(condition: str, state: dict[str, Any]) -> bool:
    condition = condition.strip()
    if not condition:
        raise ValueError("empty success criterion")
    if " exists" in condition:
        path = condition[: condition.index(" exists")].strip()
        return path in state
    for op in ("==", "!="):
        if op in condition:
            left, _, right = condition.partition(op)
            path = left.strip()
            expected = right.strip().strip("\"'")
            actual = state.get(path)
            if op == "==":
                return actual == _coerce(expected, actual)
            return actual != _coerce(expected, actual)
    # bare path -> truthiness of the value
    return bool(state.get(condition.strip()))


def _coerce(expected: str, actual: Any) -> Any:
    """Coerce the string literal from a criterion to the observed value's type."""
    if isinstance(actual, bool):
        return expected.lower() in {"true", "1", "yes"}
    if isinstance(actual, int):
        try:
            return int(expected)
        except ValueError:
            return expected
    if isinstance(actual, float):
        try:
            return float(expected)
        except ValueError:
            return expected
    return expected


@dataclass
class Goal:
    """A goal owned by an agent.

    World state and action inputs are always kept separate: a goal carries
    *constraints on observed state* and *success criteria evaluated against
    observed state*, never implicit action inputs.
    """

    id: GoalId
    agent_id: AgentId
    description: str
    priority: GoalPriority = GoalPriority.NORMAL
    status: GoalStatus = GoalStatus.CREATED
    constraints: list[GoalConstraint] = field(default_factory=list)
    success_criteria: list[SuccessCriterion] = field(default_factory=list)
    parent_id: GoalId | None = None
    subgoals: list[GoalId] = field(default_factory=list)
    dependencies: list[GoalId] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    def has_met_success_criteria(self, world_state: dict[str, Any]) -> bool:
        if not self.success_criteria:
            return False
        return all(c.evaluate(world_state) for c in self.success_criteria)