class FeasibilityEvaluator:
    def evaluate(self,plan,constraints=None):
        violations=tuple(constraints.validate(plan)) if constraints else ()
        return {"feasible":not violations,"violations":violations}
