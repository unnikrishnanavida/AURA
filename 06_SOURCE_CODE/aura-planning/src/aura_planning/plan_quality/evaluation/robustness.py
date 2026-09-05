class RobustnessEvaluation:
    def evaluate(self,outcomes): return sum(bool(x) for x in outcomes)/len(outcomes) if outcomes else 0.
