from __future__ import annotations
from typing import Callable
from ..models.goal import Goal
from ..models.subgoal import Subgoal

class GoalDecomposer:
    def __init__(self, rules: dict[str, Callable[[Goal], list[Goal]]] | None = None):
        self.rules = dict(rules or {})

    def register(self, objective_name: str, decomposer: Callable[[Goal], list[Goal]]):
        self.rules[objective_name] = decomposer

    def decompose(self, goal: Goal) -> tuple[Subgoal, ...]:
        rule = self.rules.get(str(goal.objective))
        if rule is None:
            return ()
        children = rule(goal)
        return tuple(
            Subgoal(child, goal.goal_id, index)
            for index, child in enumerate(children)
        )
