from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class FallbackStrategy:
    trigger:str
    plan:object
    risk_reduction:float=0.0
