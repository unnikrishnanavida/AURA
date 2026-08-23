class RiskCritic:
    def critique(self,plan,threshold=.5):
        return tuple(a for a in getattr(plan,"actions",plan) if getattr(a,"risk",0)>threshold)
