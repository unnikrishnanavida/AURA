class MultiObjective:
    def __init__(self,objectives): self.objectives=tuple(objectives)
    def vector(self,candidate): return tuple(o.evaluate(candidate) for o in self.objectives)
    def score(self,candidate): return sum(self.vector(candidate))
    def rank(self,candidates): return tuple(sorted(candidates,key=self.score,reverse=True))
