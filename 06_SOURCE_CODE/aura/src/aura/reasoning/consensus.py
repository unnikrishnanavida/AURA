"""Reasoning consensus.

Where multiple strategies are used, consensus compares conclusions,
identifies disagreement, measures confidence, and escalates uncertainty.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aura.reasoning.models import Conclusion
from aura.reasoning.uncertainty import UncertaintyLevel


@dataclass(frozen=True)
class ConsensusVerdict:
    agreement: str  # agreed | divided | uncertain
    answer: str | None
    confidence: float
    uncertainty: UncertaintyLevel
    contributors: tuple[str, ...]
    disagreement: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "agreement": self.agreement,
            "answer": self.answer,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty.value,
            "contributors": list(self.contributors),
            "disagreement": list(self.disagreement),
        }


def _statement_stem(statement: str) -> str:
    lower = statement.lower()
    for prefix in ("unknown:", "if ", "best explains"):
        if lower.startswith(prefix):
            return ""
    for marker in (" (by analogy)", " (prior "):
        idx = lower.find(marker)
        if idx != -1:
            return lower[:idx].strip()
    return lower.strip()


class ConsensusEngine:
    def decide(self, conclusions: Iterable[Conclusion]) -> ConsensusVerdict:
        conclusions = [c for c in conclusions]
        if not conclusions:
            return ConsensusVerdict("uncertain", None, 0.0, UncertaintyLevel.HIGH, ())

        by_stem: dict[str, list[Conclusion]] = {}
        for conclusion in conclusions:
            stem = _statement_stem(conclusion.statement)
            if stem:
                by_stem.setdefault(stem, []).append(conclusion)

        strong = [
            c
            for c in conclusions
            if c.confidence >= 0.4 and c.uncertainty is not UncertaintyLevel.HIGH
        ]
        if not strong:
            return ConsensusVerdict(
                "uncertain",
                None,
                0.0,
                UncertaintyLevel.HIGH,
                tuple(c.strategy for c in conclusions),
                disagreement=tuple({c.statement for c in conclusions}),
            )

        ranked_stems = sorted(
            by_stem.items(),
            key=lambda item: sum(c.confidence for c in item[1]),
            reverse=True,
        )
        top_stem, top_conclusions = ranked_stems[0]
        top_confidence = sum(c.confidence for c in top_conclusions) / len(top_conclusions)
        contributors = tuple(sorted(c.strategy for c in top_conclusions))
        disagreement = tuple(
            stem for stem, _items in ranked_stems[1:] if _items[0].confidence >= 0.4
        )

        agreement = "agreed" if not disagreement else "divided"
        if len(strong) == 1 and len(top_conclusions) == 1:
            agreement = "uncertain" if top_confidence < 0.4 else "agreed"

        return ConsensusVerdict(
            agreement=agreement,
            answer=top_stem,
            confidence=round(top_confidence, 6),
            uncertainty=(
                UncertaintyLevel.LOW
                if agreement == "agreed" and top_confidence >= 0.7
                else UncertaintyLevel.MEDIUM
            ),
            contributors=contributors,
            disagreement=disagreement,
        )


__all__ = ["ConsensusEngine", "ConsensusVerdict"]