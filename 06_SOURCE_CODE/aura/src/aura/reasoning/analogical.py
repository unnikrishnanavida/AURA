"""Analogical strategy: structure mapping over labeled cases.

Transfers the outcome of the most similar stored case when similarity crosses
an explicit threshold; otherwise it reports no comparable case.
"""

from __future__ import annotations

from aura.reasoning.models import ReasoningInput, make_conclusion


class AnalogicalStrategy:
    name = "analogical"

    def __init__(self, similarity_threshold: float = 0.3) -> None:
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be in [0,1]")
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def reason(self, inp: ReasoningInput) -> object:
        target = frozenset(inp.observed_propositions)
        if not inp.cases:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: no stored cases to compare with {inp.question!r}",
                confidence=0.0,
                reasoning=["analogical reasoning requires a case library"],
            )

        scored = [(self._jaccard(target, case.attrs) * case.strength, case) for case in inp.cases]
        scored.sort(key=lambda item: item[0], reverse=True)
        best_sim, best_case = scored[0]

        if best_sim < self.similarity_threshold:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: no sufficiently similar case for {inp.question!r}",
                confidence=0.0,
                reasoning=[f"best similarity {best_sim:.2f} below threshold {self.similarity_threshold:.2f}"],
                alternatives=[c.outcome for _s, c in scored[:3] if _s > 0.0],
            )

        alternatives = [
            case.outcome
            for sim, case in scored[1:4]
            if sim >= self.similarity_threshold and case.outcome != best_case.outcome
        ]
        return make_conclusion(
            strategy=self.name,
            statement=f"{inp.question}: {best_case.outcome} (by analogy)",
            confidence=best_sim,
            reasoning=[
                f"case {best_case.outcome} matches target on "
                f"{len(target & set(best_case.attrs))} shared attributes",
                f"jaccard similarity {best_sim:.2f}",
            ],
            supports=[best_case.outcome],
            alternatives=alternatives,
        )


__all__ = ["AnalogicalStrategy"]