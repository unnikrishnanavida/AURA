from __future__ import annotations
from ..states.comparison.state_comparator import StateComparator
from .models.goal import Goal, GoalStatus
from .decomposition.goal_decomposer import GoalDecomposer
from .prioritization.goal_ranker import GoalRanker

class GoalManager:
    def __init__(self, decomposer=None):
        self._goals: dict[str, Goal] = {}
        self.decomposer = decomposer or GoalDecomposer()
        self.ranker = GoalRanker()
        self.comparator = StateComparator()

    def register(self, goal: Goal):
        if goal.goal_id in self._goals:
            raise ValueError(f"goal already exists: {goal.goal_id}")
        self._goals[goal.goal_id] = goal

    def get(self, goal_id): return self._goals[goal_id]
    def all(self): return tuple(self._goals.values())

    def activate_ready(self, completed=()):
        done = set(completed)
        changed = []
        for goal in self._goals.values():
            if goal.status == GoalStatus.PENDING and goal.dependency_satisfied(done):
                self._goals[goal.goal_id] = goal.with_status(GoalStatus.ACTIVE)
                changed.append(goal.goal_id)
        return tuple(changed)

    def update_from_state(self, state):
        changed = []
        for goal in tuple(self._goals.values()):
            if goal.is_complete(state):
                new = goal.with_status(GoalStatus.COMPLETED)
            elif goal.has_failed(state):
                new = goal.with_status(GoalStatus.FAILED)
            else:
                continue
            self._goals[goal.goal_id] = new
            changed.append(new)
        return tuple(changed)

    def ready(self, completed=()):
        done = set(completed)
        return self.ranker.rank(
            g for g in self._goals.values()
            if g.status in {GoalStatus.PENDING, GoalStatus.ACTIVE}
            and g.dependency_satisfied(done)
        )

    def decompose(self, goal_id):
        return self.decomposer.decompose(self.get(goal_id))
