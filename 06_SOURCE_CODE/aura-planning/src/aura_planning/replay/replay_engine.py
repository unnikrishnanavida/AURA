from .runner.replay_runner import ReplayRunner
from .runner.plan_comparison import PlanComparison
class ReplayEngine:
    def __init__(self): self.runner=ReplayRunner(); self.comparison=PlanComparison()
    def replay(self,plan,state): return self.runner.run(plan,state)
    def compare(self,left,right): return self.comparison.compare(left,right)
