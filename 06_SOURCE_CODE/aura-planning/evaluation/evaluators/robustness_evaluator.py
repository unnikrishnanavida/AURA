class RobustnessEvaluator:
    def evaluate(self,outcomes):
        if not outcomes:return {"robustness":0.0,"samples":0}
        return {"robustness":sum(bool(x) for x in outcomes)/len(outcomes),"samples":len(outcomes)}
