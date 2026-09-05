"""Planning domain models."""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.foundation.ids import GoalId, PlanId

__all__ = ["Constraint", "Goal", "Plan", "PlanRisk", "PlanStep", "Task"]


@dataclass(frozen=True, slots=True)
class Goal:
    id: GoalId
    description: str
    success_criteria: tuple[str, ...] = ()

    @classmethod
    def create(cls, *, description: str, success_criteria: tuple[str, ...] = ()) -> Goal:
        if not description.strip():
            raise ValueError("goal description must not be empty")
        return cls(id=GoalId.new(), description=description, success_criteria=success_criteria)


@dataclass(frozen=True, slots=True)
class Task:
    name: str
    prerequisites: tuple[str, ...] = ()
    capability: str = "domain.execute"
    estimated_cost: float = 1.0
    estimated_seconds: float = 1.0
    risk: float = 0.2
    rollback_feasible: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlanStep:
    order: int
    task: Task
    status: str = "pending"

    def prerequisites_met(self, executed: set[str]) -> bool:
        return all(p in executed for p in self.task.prerequisites)


@dataclass(frozen=True, slots=True)
class Constraint:
    kind: str  # max_cost | max_time | required_capability | forbid_capability
    value: object


@dataclass(frozen=True, slots=True)
class PlanRisk:
    level: str  # low | medium | high
    score: float
    cost_estimate: float
    time_estimate: float
    required_capabilities: tuple[str, ...]
    required_permissions: tuple[str, ...]
    rollback_feasible: bool
    concerns: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Plan:
    id: PlanId
    goal: Goal
    steps: tuple[PlanStep, ...]
    risk: PlanRisk = field(
        default_factory=lambda: PlanRisk(
            level="low",
            score=0.0,
            cost_estimate=0.0,
            time_estimate=0.0,
            required_capabilities=(),
            required_permissions=(),
            rollback_feasible=True,
        )
    )

    @property
    def names(self) -> list[str]:
        return [f"{step.order}:{step.task.name}" for step in self.steps]