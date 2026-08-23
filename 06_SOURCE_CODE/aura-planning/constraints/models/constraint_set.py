from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class ConstraintSet:
    hard: tuple = ()
    soft: tuple = ()
    def validate(self,candidate):
        return tuple(h.constraint.message for h in self.hard if h.violated(candidate))
    def penalty(self,candidate):
        return sum(s.penalty_for(candidate) for s in self.soft)
