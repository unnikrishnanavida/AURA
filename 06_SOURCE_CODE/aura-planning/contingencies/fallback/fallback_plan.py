from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class FallbackPlan:
    plan: object
    trigger: str
    risk: float = 0.0
    def acceptable(self, threshold=0.5): return self.risk <= threshold
