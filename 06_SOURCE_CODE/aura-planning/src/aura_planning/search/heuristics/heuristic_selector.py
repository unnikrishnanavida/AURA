class HeuristicSelector:
    def __init__(self,heuristics): self.heuristics=tuple(heuristics)
    def select(self,name): return next(h for h in self.heuristics if h.__class__.__name__==name)
    def best(self,state,goal): return min((h.estimate(state,goal),h) for h in self.heuristics)[1]
