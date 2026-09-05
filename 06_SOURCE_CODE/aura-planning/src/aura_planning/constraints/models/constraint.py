from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True, slots=True)
class Constraint:
    name: str
    predicate: Callable[[object], bool]
    message: str = "constraint violated"
    priority: float = 1.0

    def evaluate(self, candidate):
        return bool(self.predicate(candidate))
