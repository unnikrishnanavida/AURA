from ..analysis.risk_analyzer import analyze
from ..analysis.unsafe_action_detector import detect
from ..models.safety_decision import SafetyDecision


class ExecutionSafetyGate:
    def __init__(self, deny_threshold=.9, review_threshold=.7):
        self.deny_threshold=deny_threshold; self.review_threshold=review_threshold
    def evaluate(self,action,approved=False):
        risk=analyze(action); violations=detect(action)
        if violations or risk.score>=self.deny_threshold:
            return SafetyDecision("DENY",risk.score,tuple(violations or risk.factors),tuple(violations),False)
        if risk.score>=self.review_threshold and not approved:
            return SafetyDecision("REVIEW",risk.score,risk.factors,(),True)
        return SafetyDecision("ALLOW",risk.score,risk.factors,(),False)
