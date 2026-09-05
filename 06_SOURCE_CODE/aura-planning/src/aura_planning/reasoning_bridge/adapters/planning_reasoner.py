from ..contracts.reasoning_result import ReasoningResult
class PlanningReasoner:
    def __init__(self, planner):
        self.planner = planner
    def supports(self, request):
        return hasattr(self.planner, "plan")
    def reason(self, request):
        plan = self.planner.plan(request.problem)
        return ReasoningResult(plan, 1.0 if plan is not None else 0.0)
