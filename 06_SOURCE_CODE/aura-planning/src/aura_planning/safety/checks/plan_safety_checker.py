class PlanSafetyChecker:
    def check(self, plan, policies):
        violations=[]
        for policy in policies: violations.extend(policy.evaluate(plan))
        return {"safe":not violations,"violations":tuple(violations)}
