from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class RiskAssessment:
    risks: tuple
    score: float
    def critical(self, threshold=.5): return tuple(r for r in self.risks if r.exposure >= threshold)
