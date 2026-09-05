from dataclasses import dataclass
@dataclass(slots=True)
class PlanningBudget:
    max_expansions:int=10000
    max_seconds:float=30.0
    expansions:int=0
    def consume(self,n=1):
        self.expansions+=n
        if self.expansions>self.max_expansions: raise RuntimeError("planning expansion budget exceeded")
