from dataclasses import dataclass, field
from .goal import Goal

@dataclass(frozen=True, slots=True)
class Subgoal:
    goal: Goal
    parent_id: str
    order: int = 0
    decomposition_cost: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def goal_id(self): return self.goal.goal_id
