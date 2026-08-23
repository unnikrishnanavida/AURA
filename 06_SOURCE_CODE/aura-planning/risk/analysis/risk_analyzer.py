class RiskAnalyzer:
    def assess(self,plan):
        actions=tuple(getattr(plan,"actions",plan))
        probability=1.0
        for action in actions: probability*=1-float(getattr(action,"risk",0))
        return {"success_probability":probability,"failure_probability":1-probability,
                "exposure":sum(float(getattr(a,"risk",0)) for a in actions)}
