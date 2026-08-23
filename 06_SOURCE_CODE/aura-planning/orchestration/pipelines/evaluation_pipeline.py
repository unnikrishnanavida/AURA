class EvaluationPipeline:
    def __init__(self,evaluators=()): self.evaluators=tuple(evaluators)
    def run(self,plan): return {e.__class__.__name__:e.evaluate(plan) for e in self.evaluators}
