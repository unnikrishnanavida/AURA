"""aura-planning — planning subsystem for AURA.

Provides goal decomposition, constraint validation, capability-gap detection,
candidate plan generation, risk analysis, plan comparison, contingency plans,
and replanning. The planner honestly represents unsatisfied constraints,
missing capabilities, high risk, and uncertainty instead of pretending
impossible plans are executable.
"""

from __future__ import annotations

from aura_planning.goals.models.goal import Goal, GoalStatus
from aura_planning.planning.planner import ActionSpec, Planner
from aura_planning.plans.plan import CapabilityGap, Plan, UnsatisfiedConstraint

__all__ = [
    "ActionSpec",
    "CapabilityGap",
    "Goal",
    "GoalStatus",
    "Plan",
    "Planner",
    "UnsatisfiedConstraint",
]