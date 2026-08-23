class ConstraintSolver:
    def solve(self, candidates, constraints):
        feasible=[c for c in candidates if not constraints.validate(c)]
        if not feasible: return None
        return min(feasible,key=constraints.penalty)
