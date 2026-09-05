from .tradeoffs.pareto_frontier import ParetoFrontier
class PlanningOptimizer:
    def __init__(self,objective): self.objective=objective; self.frontier=ParetoFrontier()
    def optimize(self,candidates):
        return self.objective.rank(candidates)
    def pareto(self,candidates,vectors):
        front=self.frontier.compute(vectors)
        return tuple(c for c,v in zip(candidates,vectors) if v in front)
