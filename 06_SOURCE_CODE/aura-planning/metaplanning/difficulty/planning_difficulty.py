from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanningDifficulty:
    branching:float
    depth:float
    uncertainty:float
    def score(self): return .4*self.branching+.35*self.depth+.25*self.uncertainty
