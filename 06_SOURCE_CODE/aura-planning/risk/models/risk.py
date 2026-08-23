from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class Risk:
    name: str
    probability: float
    impact: float
    metadata: dict = field(default_factory=dict)
    def __post_init__(self):
        if not 0 <= self.probability <= 1 or not 0 <= self.impact <= 1:
            raise ValueError("probability and impact must be in [0,1]")
    @property
    def exposure(self): return self.probability * self.impact
