from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ReasoningResult:
    conclusion:object
    confidence:float
    assumptions:tuple=()
    constraints:tuple=()
    recommendations:tuple=()
