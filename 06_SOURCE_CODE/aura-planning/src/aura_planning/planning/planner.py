"""The aura-planning planner facade.

Runs the full mission flow:

    GOAL
      -> DECOMPOSITION
      -> CONSTRAINT VALIDATION
      -> CANDIDATE PLANS
      -> CAPABILITY GAP DETECTION
      -> RISK ANALYSIS
      -> PLAN COMPARISON
      -> SELECTED PLAN
      -> CONTINGENCY PLAN

The planner NEVER pretends an impossible plan is executable. Every returned
:class:`Plan` carries explicit unsatisfied-constraint, missing-capability,
risk, and uncertainty signals, plus alternatives and a contingency plan when
they exist.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from aura_planning.constraints.models.constraint_set import ConstraintSet
from aura_planning.goals.decomposition.goal_decomposer import GoalDecomposer
from aura_planning.goals.models.goal import Goal
from aura_planning.plans.plan import CapabilityGap, Plan, UnsatisfiedConstraint
from aura_planning.risk.models.plan_risk import PlanRisk


@dataclass(frozen=True)
class ActionSpec:
    """A planned action with its capability requirement and risk."""

    action_id: str
    capability: str
    risk: float = 0.0
    cost: float = 0.0
    duration: float = 0.0


@dataclass
class Planner:
    """Builds candidate plans for a goal, honestly representing limits."""

    goal: Goal
    constraints: ConstraintSet | None = None
    available_capabilities: set[str] = field(default_factory=set)
    decomposer: GoalDecomposer | None = None
    risk_threshold: float = 0.9

    # ------------------------------------------------------------------
    # decomposition
    # ------------------------------------------------------------------
    def decompose(self) -> tuple[Any, ...]:
        if self.decomposer is None:
            return ()
        return self.decomposer.decompose(self.goal)
# ------------------------------------------------------------------
    # candidate generation
    # ------------------------------------------------------------------
    def candidates(self, action_sets: Iterable[Iterable[Any]]) -> list[Plan]:
        """Turn each proposed action set into a candidate Plan."""
        plans: list[Plan] = []
        for actions in action_sets:
            plans.append(self._build_plan(tuple(actions), base_goal=True))
        return plans

    def _build_plan(self, actions: tuple[Any, ...], *, base_goal: bool) -> Plan:
        plan_id = f"pl-{uuid4().hex[:12]}"
        unsatisfied = self._validate_constraints(actions)
        gaps = self._detect_capability_gaps(actions)
        risk = self._assess_risk(actions)
        uncertainty = self._assess_uncertainty(actions)
        subgoals = self.decompose() if base_goal else ()
        return Plan(
            plan_id=plan_id,
            goal=self.goal,
            actions=actions,
            subgoals=subgoals,
            unsatisfied_constraints=unsatisfied,
            missing_capabilities=gaps,
            risk=risk,
            uncertainty=uncertainty,
        )
# ------------------------------------------------------------------
    # validation / capability-gap detection
    # ------------------------------------------------------------------
    def _validate_constraints(self, actions: tuple[Any, ...]) -> tuple[UnsatisfiedConstraint, ...]:
        if self.constraints is None:
            return ()
        violations = self.constraints.validate(actions)
        return tuple(UnsatisfiedConstraint(name=f"constraint-{i}", message=str(v)) for i, v in enumerate(violations))

    def _detect_capability_gaps(self, actions: tuple[Any, ...]) -> tuple[CapabilityGap, ...]:
        gaps: list[CapabilityGap] = []
        for action in actions:
            capability = self._action_capability(action)
            if capability and capability not in self.available_capabilities:
                gaps.append(CapabilityGap(capability=capability, requested_by=self._action_id(action)))
        return tuple(gaps)

    @staticmethod
    def _action_capability(action: Any) -> str | None:
        cap = getattr(action, "capability", None)
        if cap:
            return str(cap)
        return None

    @staticmethod
    def _action_id(action: Any) -> str:
        return str(getattr(action, "action_id", action))
# ------------------------------------------------------------------
    # risk / uncertainty
    # ------------------------------------------------------------------
    def _assess_risk(self, actions: tuple[Any, ...]) -> PlanRisk | None:
        if not actions:
            return None
        risks = [float(getattr(a, "risk", 0.0)) for a in actions]
        return PlanRisk(factors=tuple(risks), exposure=sum(risks))

    def _assess_uncertainty(self, actions: tuple[Any, ...]) -> float:
        """Uncertainty grows with unverified actions and missing capabilities."""
        if not actions:
            return 1.0
        unverified = sum(1 for a in actions if not getattr(a, "verified", False))
        gap_penalty = len(self._detect_capability_gaps(actions)) * 0.2
        return round(min(1.0, unverified / len(actions) + gap_penalty), 3)

    # ------------------------------------------------------------------
    # selection + contingency
    # ------------------------------------------------------------------
    def select(self, plans: Iterable[Plan], *, score_fn: Callable[[Plan], float] | None = None) -> Plan:
        """Pick the best feasible plan by score; never pick an infeasible one
        while a feasible one exists."""
        plans = list(plans)
        feasible = [p for p in plans if p.feasible]
        score = score_fn or (lambda p: p.score or 0.0)
        if feasible:
            best = max(feasible, key=score)
            best.score = score(best)
            return best
        # No feasible plan: return the least-bad infeasible plan clearly marked.
        best_plan: Plan | None = max(plans, key=score, default=None) if plans else None
        if best_plan is None:
            raise ValueError("no candidates to select from")
        best_plan.score = score(best_plan)
        return best_plan

    def with_contingency(self, plan: Plan, contingency: Plan) -> Plan:
        plan.contingency = contingency
        return plan

    def replan_after_failure(self, plan: Plan, *, failed_action_id: str, alternatives: Iterable[Plan]) -> Plan:
        """Replan after a failure: exclude the failed path, keep alternatives."""
        failed = [p for p in alternatives if failed_action_id not in [self._action_id(a) for a in p.actions]]
        if not failed:
            return plan  # no better alternative; keep the original (marked)
        best = self.select(failed)
        best.metadata["replanned_after"] = failed_action_id
        return best


__all__ = ["ActionSpec", "Planner"]