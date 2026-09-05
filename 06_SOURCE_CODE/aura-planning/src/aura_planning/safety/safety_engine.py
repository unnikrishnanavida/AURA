from .checks.plan_safety_checker import PlanSafetyChecker
class SafetyEngine:
    def __init__(self, policies=()):
        self.policies=tuple(policies)
        self.checker=PlanSafetyChecker()
    def check(self, plan):
        return self.checker.check(plan,self.policies)
    def require_safe(self, plan):
        report=self.check(plan)
        if not report["safe"]:
            raise PermissionError(f"unsafe plan: {report['violations']}")
        return plan
