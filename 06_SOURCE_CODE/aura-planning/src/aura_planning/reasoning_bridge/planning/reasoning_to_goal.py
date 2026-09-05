from ..input.reasoning_result import ReasoningResult
class ReasoningToGoal:
    def convert(self,result:ReasoningResult,goal_id="reasoned-goal"):
        from aura_planning.goals.models.goal import Goal
        return Goal(goal_id,result.conclusion, result.conclusion, result.confidence, constraints=result.constraints)
