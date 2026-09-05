class ProbabilisticPlanner:
    def __init__(self,forward_planner,probability_model):
        self.forward=forward_planner; self.probability=probability_model
    def rank(self,candidates):
        return sorted(candidates,key=lambda p:self.probability(p),reverse=True)
