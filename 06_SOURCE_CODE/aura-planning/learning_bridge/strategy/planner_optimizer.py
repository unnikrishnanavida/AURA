class PlannerOptimizer:
    def __init__(self,learner): self.learner=learner
    def observe(self,strategy,reward): self.learner.update(strategy,reward)
    def recommend(self): return self.learner.best()
