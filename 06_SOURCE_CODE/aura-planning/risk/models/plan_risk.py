from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanRisk:
    factors:tuple
    exposure:float
    confidence:float=1.0
    def exceeds(self,threshold): return self.exposure>threshold
