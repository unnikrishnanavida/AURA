from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanScore:
    value:float; feasibility:float; efficiency:float; robustness:float
