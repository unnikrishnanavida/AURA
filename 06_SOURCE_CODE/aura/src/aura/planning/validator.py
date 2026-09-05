"""Plan validation.

Validates ordering integrity and constraints. Validation fails fast with
structured reasons; an invalid plan is never proposed for execution.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.planning.models import Constraint, Goal, Task


@dataclass(frozen=True)
class PlanValidation:
    valid: bool
    issues: tuple[str, ...] = ()

    @property
    def summary(self) -> str:
        return "plan valid" if self.valid else "; ".join(self.issues)


class PlanValidator:
    def validate(
        self,
        *,
        goal: Goal,
        tasks: list[Task],
        constraints: tuple[Constraint, ...] = (),
        requested_capabilities: set[str] | None = None,
    ) -> PlanValidation:
        issues: list[str] = []
        if not goal.description.strip():
            issues.append("goal description is empty")
        if not tasks:
            issues.append("plan has no tasks")
        names = [t.name for t in tasks]
        if len(set(names)) != len(names):
            issues.append("plan contains duplicate task names")

        available = set(names)
        for task in tasks:
            for prereq in task.prerequisites:
                if prereq not in available:
                    issues.append(f"task {task.name!r} depends on unknown task {prereq!r}")

        total_cost = sum(t.estimated_cost for t in tasks)
        total_time = sum(t.estimated_seconds for t in tasks)
        required_caps = {t.capability for t in tasks}
        for constraint in constraints:
            if constraint.kind == "max_cost":
                assert isinstance(constraint.value, (int, float))
                if total_cost > constraint.value:
                    issues.append(f"plan cost {total_cost:.2f} exceeds max_cost {constraint.value}")
            elif constraint.kind == "max_time":
                assert isinstance(constraint.value, (int, float))
                if total_time > constraint.value:
                    issues.append(f"plan time {total_time:.1f}s exceeds max_time {constraint.value}")
            elif constraint.kind == "forbid_capability":
                assert isinstance(constraint.value, str)
                if constraint.value in required_caps:
                    issues.append(f"plan requires forbidden capability {constraint.value!r}")

        if requested_capabilities is not None:
            missing = sorted(required_caps - requested_capabilities)
            if missing:
                issues.append(f"plan requires capabilities not held: {missing}")

        return PlanValidation(valid=not issues, issues=tuple(issues))


__all__ = ["PlanValidation", "PlanValidator"]