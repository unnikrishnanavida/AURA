class ActionSafetyChecker:
    def check(self, action, policies):
        violations=[]
        for policy in policies: violations.extend(policy.evaluate(action))
        return not violations, tuple(violations)
