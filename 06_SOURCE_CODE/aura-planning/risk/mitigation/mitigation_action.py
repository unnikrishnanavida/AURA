from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class MitigationAction:
    risk_name: str
    action: object
    reduction: float
    def residual(self, risk):
        return max(0.0, risk.exposure * (1 - self.reduction))
