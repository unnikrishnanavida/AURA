"""Plan model for aura-planning.

A :class:`Plan` is a candidate sequence of actions with an honest feasibility
assessment. It NEVER pretends an impossible plan is executable: unsatisfied
constraints, missing capabilities, high risk, and uncertainty are all
represented explicitly rather than hidden or silently ignored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_planning.goals.models.goal import Goal
from aura_planning.risk.models.plan_risk import PlanRisk


@dataclass(frozen=True)
class CapabilityGap:
    """A required capability that is not available."""

    capability: str
    requested_by: str  # action id or "goal"

    def __str__(self) -> str:
        return f"missing capability {self.capability!r} (required by {self.requested_by})"


@dataclass(frozen=True)
class UnsatisfiedConstraint:
    """A constraint that cannot be satisfied by this plan."""

    name: str
    message: str

    def __str__(self) -> str:
        return f"unsatisfied constraint {self.name!r}: {self.message}"


@dataclass
class Plan:
    """A candidate plan with explicit feasibility signals."""

    plan_id: str
    goal: Goal
    actions: tuple[Any, ...] = ()
    subgoals: tuple[Any, ...] = ()
    unsatisfied_constraints: tuple[UnsatisfiedConstraint, ...] = ()
    missing_capabilities: tuple[CapabilityGap, ...] = ()
    risk: PlanRisk | None = None
    uncertainty: float = 0.0  # 0..1, first-class
    score: float | None = None
    contingency: Plan | None = None
    alternatives: tuple[Plan, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def feasible(self) -> bool:
        """A plan is feasible only when all hard conditions are satisfied."""
        if self.unsatisfied_constraints:
            return False
        if self.missing_capabilities:
            return False
        return bool(self.actions or self.subgoals)

    @property
    def actionable(self) -> bool:
        """Feasible AND not blocked by excessive risk/uncertainty."""
        if not self.feasible:
            return False
        if self.risk is not None and self.risk.exceeds(0.9):
            return False
        return self.uncertainty < 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": getattr(self.goal, "objective", str(self.goal)),
            "actions": [getattr(a, "action_id", str(a)) if not isinstance(a, str) else a for a in self.actions],
            "feasible": self.feasible,
            "actionable": self.actionable,
            "unsatisfied_constraints": [str(c) for c in self.unsatisfied_constraints],
            "missing_capabilities": [str(c) for c in self.missing_capabilities],
            "risk": None if self.risk is None else self.risk.exposure,
            "uncertainty": self.uncertainty,
            "score": self.score,
            "has_contingency": self.contingency is not None,
            "alternatives": len(self.alternatives),
        }


__all__ = [
    "CapabilityGap",
    "Plan",
    "UnsatisfiedConstraint",
]