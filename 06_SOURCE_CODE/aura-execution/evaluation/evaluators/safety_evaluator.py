class SafetyEvaluator:
    def evaluate(self,decision):return decision.decision in {"ALLOW","REVIEW","DENY"}
