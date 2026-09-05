class FeasibilityChecker:
    def check(self,candidate,constraints):
        violations=tuple(constraints.validate(candidate))
        return {"feasible":not violations,"violations":violations,"penalty":constraints.penalty(candidate)}
