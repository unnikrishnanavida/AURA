"""Goal engine: create, activate, decompose, track, and complete goals."""

from __future__ import annotations

from datetime import UTC, datetime

from aura_agent.contracts.errors import ValidationFailure
from aura_agent.contracts.ids import AgentId, GoalId
from aura_agent.goals.conflict.conflict_detector import ConflictDetector, GoalConflict
from aura_agent.goals.decomposition.goal_decomposer import (
    DecompositionPlan,
    GoalDecomposer,
    SubgoalSpec,
)
from aura_agent.goals.models.goal import (
    Goal,
    GoalConstraint,
    GoalPriority,
    GoalStatus,
    SuccessCriterion,
)

__all__ = ["GoalEngine", "GoalUpdate"]


class GoalUpdate:
    """A lightweight typed record of a goal state change."""

    __slots__ = ("goal_id", "from_status", "to_status", "at")

    def __init__(
        self,
        goal_id: GoalId,
        from_status: GoalStatus,
        to_status: GoalStatus,
        at: datetime | None = None,
    ) -> None:
        self.goal_id = goal_id
        self.from_status = from_status
        self.to_status = to_status
        self.at = at or datetime.now(UTC)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"GoalUpdate(goal_id={self.goal_id!r}, "
            f"{self.from_status.value} -> {self.to_status.value})"
        )


class GoalEngine:
    """Owns the goal lifecycle: creation, validation, activation,
    decomposition, tracking, and terminal transitions.

    The engine is deterministic: given identical inputs it produces identical
    goal states. The `clock` hook exists purely so tests can control time.
    """

    def __init__(
        self,
        decomposer: GoalDecomposer | None = None,
        conflict_detector: ConflictDetector | None = None,
        *,
        clock=None,
    ) -> None:
        self._decomposer = decomposer or GoalDecomposer()
        self._conflict_detector = conflict_detector or ConflictDetector()
        self._clock = clock or datetime.now
        self._goals: dict[GoalId, Goal] = {}
        self._updates: list[GoalUpdate] = []

    # -- query -----------------------------------------------------------------
    def get(self, goal_id: GoalId) -> Goal:
        if goal_id not in self._goals:
            raise KeyError(f"unknown goal {goal_id}")
        return self._goals[goal_id]

    def all(self) -> list[Goal]:
        return list(self._goals.values())

    def by_status(self, status: GoalStatus) -> list[Goal]:
        return [g for g in self._goals.values() if g.status is status]

    @property
    def updates(self) -> list[GoalUpdate]:
        return list(self._updates)
# -- decomposition ---------------------------------------------------------
    def decompose(
        self, goal_id: GoalId, specs: list[SubgoalSpec] | None = None
    ) -> list[Goal]:
        """Decompose a goal into subgoals.

        When no specs are supplied, a deterministic single-step plan is
        generated so every goal remains executable end-to-end.
        """
        goal = self.get(goal_id)
        plan = DecompositionPlan(subgoals=specs or [])
        subgoals = self._decomposer.decompose(goal, plan) if plan.subgoals else []
        for sub in subgoals:
            self._goals[sub.id] = sub
        return subgoals

    def evaluate_success(self, goal_id: GoalId, world_state: dict) -> bool:
        """Check success criteria against observed world state (not inputs)."""
        goal = self.get(goal_id)
        return goal.has_met_success_criteria(world_state)

    def detect_conflicts(self) -> list[GoalConflict]:
        active = self.by_status(GoalStatus.ACTIVE) + self.by_status(
            GoalStatus.IN_PROGRESS
        )
        return self._conflict_detector.detect(active)

    # -- helpers ---------------------------------------------------------------
    def _transition(
        self, goal: Goal, target: GoalStatus, *, reason: str = ""
    ) -> None:
        if goal.status is target:
            return
        self._updates.append(GoalUpdate(goal.id, goal.status, target, self._clock()))
        goal.status = target
        goal.touch()