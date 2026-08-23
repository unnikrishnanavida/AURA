from dataclasses import dataclass
from .risk_level import level, RiskLevel
@dataclass(frozen=True)
class ExecutionRisk:
    score: float
    factors: tuple[str,...]=()
    @property
    def level(self)->RiskLevel:return level(self.score)
