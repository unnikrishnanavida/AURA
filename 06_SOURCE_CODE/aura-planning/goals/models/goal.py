from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Iterable

class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass(frozen=True, slots=True)
class Goal:
    goal_id: str
    objective: Any
    desired_state: Any
    priority: float = 0.5
    deadline: datetime | None = None
    success_criteria: tuple[Callable[[Any], bool], ...] = ()
    failure_criteria: tuple[Callable[[Any], bool], ...] = ()
    dependencies: tuple[str, ...] = ()
    constraints: tuple[Any, ...] = ()
    status: GoalStatus = GoalStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.goal_id.strip():
            raise ValueError("goal_id is required")
        if not 0 <= self.priority <= 1:
            raise ValueError("priority must be between 0 and 1")
        object.__setattr__(self, "dependencies", tuple(dict.fromkeys(self.dependencies)))

    def with_status(self, status: GoalStatus) -> "Goal":
        return replace(self, status=status)

    def is_complete(self, state: Any) -> bool:
        return bool(self.success_criteria) and all(check(state) for check in self.success_criteria)

    def has_failed(self, state: Any) -> bool:
        return any(check(state) for check in self.failure_criteria)

    def overdue(self, now: datetime | None = None) -> bool:
        return self.deadline is not None and (now or datetime.now(self.deadline.tzinfo)) > self.deadline

    def dependency_satisfied(self, completed: Iterable[str]) -> bool:
        done = set(completed)
        return all(dep in done for dep in self.dependencies)
