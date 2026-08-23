from .goal_priority import GoalPriority
from ..models.goal import Goal
def resolve_priority(goal:Goal,urgency:float=0,risk:float=0)->GoalPriority:
    if not all(0<=v<=1 for v in (goal.priority,urgency,risk)): raise ValueError("priority values must be [0,1]")
    return GoalPriority(urgency,goal.priority,risk)
