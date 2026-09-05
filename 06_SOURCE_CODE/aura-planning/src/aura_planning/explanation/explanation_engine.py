from .generation.plan_explainer import PlanExplainer
from .generation.decision_explanation import DecisionExplanation
class ExplanationEngine:
    def __init__(self):
        self.plan=PlanExplainer(); self.decision=DecisionExplanation()
    def explain_plan(self,plan): return self.plan.explain(plan)
    def explain_decision(self,selected,candidates,score): return self.decision.explain(selected,candidates,score)
