"""Planning engine.

Produces a validated primary plan and up to two deterministic alternatives
when independent tasks can be reordered, then ranks them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.foundation.ids import PlanId
from aura.planning.compare import PlanComparator
from aura.planning.decomposer import GoalDecomposer
from aura.planning.models import Constraint, Goal, Plan, PlanStep, Task
from aura.planning.risk import RiskAnalyzer
from aura.planning.validator import PlanValidation, PlanValidator


@dataclass
class PlanResult:
    goal: Goal
    primary: Plan | None
    alternatives: list[Plan] = field(default_factory=list)
    validation: PlanValidation | None = None
    issues: tuple[str, ...] = ()

    @property
    def all_plans(self) -> list[Plan]:
        return [p for p in [self.primary, *self.alternatives] if p is not None]


class PlanningEngine:
    def __init__(
        self,
        decomposer: GoalDecomposer | None = None,
        validator: PlanValidator | None = None,
        risk: RiskAnalyzer | None = None,
        comparator: PlanComparator | None = None,
    ) -> None:
        self._decomposer = decomposer or GoalDecomposer()
        self._validator = validator or PlanValidator()
        self._risk = risk or RiskAnalyzer()
        self._comparator = comparator or PlanComparator()

    def plan(
        self,
        *,
        goal: Goal,
        tasks: list[Task],
        constraints: tuple[Constraint, ...] = (),
        requested_capabilities: set[str] | None = None,
        max_alternatives: int = 2,
    ) -> PlanResult:
        validation = self._validator.validate(
            goal=goal, tasks=tasks, constraints=constraints, requested_capabilities=requested_capabilities
        )
        if not validation.valid:
            return PlanResult(goal=goal, primary=None, validation=validation, issues=validation.issues)

        ordered = self._decomposer.decompose(goal, tasks)
        variant_lists = self._variants(ordered, max_alternatives=max_alternatives)

        plans: list[Plan] = []
        for variant in variant_lists:
            plan_risk = self._risk.analyze(variant)
            steps = tuple(PlanStep(order=i + 1, task=task) for i, task in enumerate(variant))
            plans.append(Plan(id=PlanId.new(), goal=goal, steps=steps, risk=plan_risk))

        comparisons = self._comparator.compare(plans)
        primary = comparisons[0].plan if comparisons else None
        alternatives = [c.plan for c in comparisons[1 : max_alternatives + 1]]
        return PlanResult(goal=goal, primary=primary, alternatives=alternatives, validation=validation)

    def _variants(self, ordered: list[Task], *, max_alternatives: int) -> list[list[Task]]:
        """Deterministic reordering of independent task groups for alternatives."""
        variants = [list(ordered)]
        if len(ordered) >= 2 and max_alternatives > 0:
            for i in range(len(ordered) - 1):
                left, right = ordered[i], ordered[i + 1]
                independent = (
                    right.name not in left.prerequisites and left.name not in right.prerequisites
                )
                if independent:
                    swapped = list(ordered)
                    swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
                    variants.append(swapped)
                    break
        if len(ordered) >= 3 and max_alternatives > 1:
            reversed_variant = list(reversed(ordered))
            index = {task.name: i for i, task in enumerate(ordered)}
            safe = all(
                index[task.name] > index.get(prereq, -1) or not task.prerequisites
                for task in reversed_variant
                for prereq in task.prerequisites
            )
            if safe:
                variants.append(reversed_variant)
        return variants[: max_alternatives + 1]


__all__ = ["PlanResult", "PlanningEngine"]