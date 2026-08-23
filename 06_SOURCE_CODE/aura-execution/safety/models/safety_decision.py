from dataclasses import dataclass, field
@dataclass(frozen=True)
class SafetyDecision:
    decision: str
    risk_score: float
    reasons: tuple[str,...]=()
    violated_policies: tuple[str,...]=()
    required_approval: bool=False
