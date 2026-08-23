"""Cognitive loop models: explicit stages and loop outcomes."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

__all__ = ["CognitiveStage", "LoopOutcome"]


class CognitiveStage(enum.Enum):
    """The finite set of cognitive-loop stages.

    Transitions follow a fixed cycle:
    OBSERVATION -> INTERPRETATION -> REASONING -> PLANNING -> DECISION ->
    EXECUTION -> EVALUATION -> REFLECTION -> OBSERVATION (next cycle).
    """

    OBSERVATION = "observation"
    INTERPRETATION = "interpretation"
    REASONING = "reasoning"
    PLANNING = "planning"
    DECISION = "decision"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"
    TERMINATED = "terminated"

    def next(self) -> "CognitiveStage":
        order = [
            CognitiveStage.OBSERVATION,
            CognitiveStage.INTERPRETATION,
            CognitiveStage.REASONING,
            CognitiveStage.PLANNING,
            CognitiveStage.DECISION,
            CognitiveStage.EXECUTION,
            CognitiveStage.EVALUATION,
            CognitiveStage.REFLECTION,
        ]
        idx = order.index(self)
        return order[(idx + 1) % len(order)]


@dataclass(frozen=True)
class LoopOutcome:
    """The terminating outcome of a cognitive loop."""

    success: bool
    reason: str
    iterations: int
    final_message: str = ""
    result: dict[str, Any] = field(default_factory=dict)