"""AURA learning engine.

Controlled learning: candidate signals are validated before any behavioral
change; safety-critical updates require explicit authorization; applied
updates are versioned and rollback-able.
"""

from __future__ import annotations

from aura.learning.engine import LearningEngine, LearningResult
from aura.learning.gate import SignalValidator, ValidationOutcome
from aura.learning.models import LearningSignal, SignalStatus
from aura.learning.registry import AppliedChange, LearningRegistry

__all__ = [
    "AppliedChange",
    "LearningEngine",
    "LearningRegistry",
    "LearningResult",
    "LearningSignal",
    "SignalStatus",
    "SignalValidator",
    "ValidationOutcome",
]