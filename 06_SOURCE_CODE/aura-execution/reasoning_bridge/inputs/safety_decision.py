from aura_execution.safety.models.safety_decision import SafetyDecision
def adapt_safety(decision):return SafetyDecision(decision.decision,decision.risk_score,decision.reasons,decision.violated_policies,decision.required_approval)
