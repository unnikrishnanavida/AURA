from .execution.plan_simulator import PlanSimulator
from .comparison.plan_comparator import PlanComparator
class SimulationEngine:
    def __init__(self): self.simulator=PlanSimulator(); self.comparator=PlanComparator()
    def evaluate(self,plans,state):
        results=tuple(self.simulator.simulate(plan,state.copy()) for plan in plans)
        return self.comparator.compare(results)
