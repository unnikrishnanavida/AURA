from dataclasses import dataclass
from .constraint import Constraint

@dataclass(frozen=True, slots=True)
class SoftConstraint:
    constraint: Constraint
    penalty: float = 1.0
    def penalty_for(self,candidate): return 0.0 if self.constraint.evaluate(candidate) else self.penalty
