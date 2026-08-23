from .difficulty.complexity_estimator import ComplexityEstimator
from .strategy.planner_selector import PlannerSelector
class Metaplanner:
    def __init__(self):
        self.estimator=ComplexityEstimator(); self.selector=PlannerSelector()
    def choose(self,branching,depth,uncertainty):
        difficulty=self.estimator.estimate(branching,depth,uncertainty)
        return self.selector.select(difficulty)
