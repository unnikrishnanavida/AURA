class PlanEvaluator:
    def evaluate(self,plan,goal=None,resources=None,risk=None,outcomes=()):
        actions=tuple(getattr(plan,"actions",plan))
        cost=sum(float(getattr(a,"cost",0)) for a in actions)
        duration=sum(float(getattr(a,"duration",0)) for a in actions)
        risk_score=sum(float(getattr(a,"risk",0)) for a in actions)/len(actions) if actions else 0.0
        success=sum(bool(x) for x in outcomes)/len(outcomes) if outcomes else None
        goal_coverage=None
        if goal is not None:
            final=getattr(plan,"final_state",None)
            if final is not None: goal_coverage=1.0 if goal.matches(final) else 0.0
        return {"cost":cost,"duration":duration,"risk":risk_score,"expected_success":success,"goal_coverage":goal_coverage}
