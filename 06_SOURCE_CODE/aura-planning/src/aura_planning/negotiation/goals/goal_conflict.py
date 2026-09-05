from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class GoalConflict:
    left:object; right:object; severity:float
