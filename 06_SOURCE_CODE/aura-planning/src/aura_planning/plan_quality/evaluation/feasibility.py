class FeasibilityEvaluation:
    def evaluate(self,plan,constraints=None):
        violations=list(constraints.validate(plan)) if constraints else []
        return 1.0 if not violations else 0.0
