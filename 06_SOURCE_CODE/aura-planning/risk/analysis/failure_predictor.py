class FailurePredictor:
    def predict(self,plan,history=()):
        action_risk=[float(getattr(a,"risk",0)) for a in getattr(plan,"actions",plan)]
        base=1.0
        for risk in action_risk: base*=1-risk
        empirical=(sum(bool(x) for x in history)/len(history)) if history else None
        return {"success_probability":empirical if empirical is not None else base,"failure_probability":1-(empirical if empirical is not None else base)}
