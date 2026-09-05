from dataclasses import dataclass
from .constraint import Constraint

@dataclass(frozen=True, slots=True)
class HardConstraint:
    constraint: Constraint
    def violated(self,candidate): return not self.constraint.evaluate(candidate)
