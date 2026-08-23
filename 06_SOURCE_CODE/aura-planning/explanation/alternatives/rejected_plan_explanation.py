from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class RejectedPlanExplanation:
    plan:object; reasons:tuple[str,...]; score:float|None=None
