from dataclasses import dataclass
@dataclass(slots=True)
class SimulationBudget:
    scenarios:int=100
    def consume(self,n=1):
        if n<0 or n>self.scenarios: raise ValueError("simulation budget exceeded")
        self.scenarios-=n
