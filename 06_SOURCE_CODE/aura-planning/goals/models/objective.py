from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True, slots=True)
class Objective:
    name: str
    evaluator: Callable[[Any], float]
    maximize: bool = True
    weight: float = 1.0

    def score(self, candidate):
        value = float(self.evaluator(candidate))
        return value if self.maximize else -value

    def weighted_score(self, candidate):
        return self.weight * self.score(candidate)
