from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ObjectiveFunction:
    name:str; maximize:bool=True; weight:float=1.
    evaluator:object=None
    def evaluate(self,candidate):
        value=float(self.evaluator(candidate))
        return value*self.weight if self.maximize else -value*self.weight
