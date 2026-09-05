from .planning_difficulty import PlanningDifficulty
class ComplexityEstimator:
    def estimate(self,branching,depth,uncertainty):
        return PlanningDifficulty(float(branching),float(depth),float(uncertainty))
