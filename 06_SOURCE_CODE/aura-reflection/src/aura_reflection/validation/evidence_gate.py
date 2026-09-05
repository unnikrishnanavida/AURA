"""Evidence gate: the validation boundary between reflection and learning.

Reflection may produce tentative lessons even with weak evidence, but only
lessons backed by sufficient evidence may become learning signals. The gate
enforces that:

- an episode with no usable observations yields an explicit "I do not know"
  result instead of a fabricated lesson;
- a lesson with zero confidence is never proposed for action;
- nothing is approved here; approval is the gate's job.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aura_reflection.models.reflection_result import ReflectionResult


class EvidenceVerdict(StrEnum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidationResult:
    """Verdict of the evidence gate for one reflection."""

    verdict: EvidenceVerdict
    reasons: tuple[str, ...] = ()

    @classmethod
    def default(cls) -> ValidationResult:
        return cls(verdict=EvidenceVerdict.UNKNOWN)

    @property
    def passed(self) -> bool:
        return self.verdict is EvidenceVerdict.SUFFICIENT


class EvidenceGate:
    """Validates that a reflection carries enough evidence to act on."""

    def validate(self, result: ReflectionResult) -> ValidationResult:
        reasons: list[str] = []

        if result.can_say_i_dont_know:
            reasons.append("reflection could not determine an outcome with confidence")

        usable_lessons = [l for l in result.lessons if l.confidence > 0.0]
        if not usable_lessons:
            reasons.append("no usable (positive-confidence) lesson was extracted")

        if not result.signals:
            reasons.append("no candidate improvement signal was produced")

        if reasons:
            return ValidationResult(
                verdict=EvidenceVerdict.INSUFFICIENT,
                reasons=tuple(reasons),
            )
        return ValidationResult(verdict=EvidenceVerdict.SUFFICIENT)

    def can_emit(self, result: ReflectionResult) -> bool:
        return self.validate(result).passed