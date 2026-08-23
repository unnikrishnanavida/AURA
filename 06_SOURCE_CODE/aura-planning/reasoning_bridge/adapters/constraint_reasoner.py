from ..contracts.reasoning_result import ReasoningResult
class ConstraintReasoner:
    def __init__(self, solver):
        self.solver = solver
    def supports(self, request):
        return bool(request.constraints) and hasattr(self.solver, "solve")
    def reason(self, request):
        solution = self.solver.solve(request.problem, request.constraints)
        return ReasoningResult(solution, 1.0 if solution is not None else 0.0)
