class PlanEvaluator:
    def evaluate(self,plan,goal=None):
        actions=tuple(getattr(plan,"actions",plan))
        cost=sum(getattr(a,"cost",0) for a in actions)
        duration=sum(getattr(a,"duration",0) for a in actions)
        risk=sum(getattr(a,"risk",0) for a in actions)
        return {"steps":len(actions),"cost":cost,"duration":duration,"risk":risk}
