from dataclasses import dataclass
@dataclass(frozen=True)
class ReasoningResult:
    conclusion:object
    confidence:float
    assumptions:tuple=()
