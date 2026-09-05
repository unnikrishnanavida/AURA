"""Uncertainty-first reasoning support.

AURA is allowed — and trained, by convention — to say "I do not know" instead
of inventing confidence. Uncertainty levels are derived from confidence and
explicit insufficient-evidence detection.
"""

from __future__ import annotations

from enum import StrEnum


class UncertaintyLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def uncertainty_from_confidence(confidence: float) -> UncertaintyLevel:
    if confidence < 0.4:
        return UncertaintyLevel.HIGH
    if confidence < 0.7:
        return UncertaintyLevel.MEDIUM
    return UncertaintyLevel.LOW


def insufficient_evidence(observed: int, required: int) -> bool:
    """Honest signal for 'I do not know': too few supporting observations."""
    return observed < required


__all__ = ["UncertaintyLevel", "insufficient_evidence", "uncertainty_from_confidence"]