class EfficiencyEvaluation:
    def evaluate(self,plan,cost_limit=1.,duration_limit=1.):
        cost=sum(getattr(a,"cost",0) for a in getattr(plan,"actions",()))
        duration=sum(getattr(a,"duration",0) for a in getattr(plan,"actions",()))
        return .5*max(0,1-cost/cost_limit)+.5*max(0,1-duration/duration_limit)
