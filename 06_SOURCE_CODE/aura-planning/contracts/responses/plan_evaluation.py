from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanEvaluation:
    feasible:bool; quality:float; cost:float; risk:float; violations:tuple[str,...]=()
    def validate(self):
        if not 0<=self.quality<=1 or self.cost<0 or self.risk<0: raise ValueError("invalid evaluation")
