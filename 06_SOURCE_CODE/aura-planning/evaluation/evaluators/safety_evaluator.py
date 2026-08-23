class SafetyEvaluator:
    def evaluate(self, plan, safety_rules):
        violations=[rule(plan) for rule in safety_rules]
        violations=[v for v in violations if v]
        return {"safe":not violations,"violations":violations}
