from .evaluation.plan_evaluator import PlanEvaluator
class QualityEngine:
    def __init__(self): self.evaluator=PlanEvaluator()
    def score(self,plan,weights=None,**kwargs):
        metrics=self.evaluator.evaluate(plan,**kwargs)
        weights=weights or {"cost":.2,"duration":.15,"risk":.25,"expected_success":.2,"goal_coverage":.2}
        score=0.0
        for key,weight in weights.items():
            value=metrics.get(key)
            if value is None: continue
            score += weight * (value if key in {"expected_success","goal_coverage"} else 1.0-max(0.0,min(1.0,float(value))))
        return {"score":max(0.0,min(1.0,score)),"metrics":metrics}
