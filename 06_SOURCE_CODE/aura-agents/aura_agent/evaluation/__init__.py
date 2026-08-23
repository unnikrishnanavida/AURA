"""Evaluation: expected-vs-observed state, goal progress, and drift signals."""

from aura_agent.evaluation.evaluation_engine import (
    EvaluationEngine,
    path_exists,
    resolve_path,
)
from aura_agent.evaluation.models import (
    EvaluationResult,
    EvaluationVerdict,
    StateExpectation,
)

__all__ = [
    "EvaluationVerdict",
    "StateExpectation",
    "EvaluationResult",
    "EvaluationEngine",
    "resolve_path",
    "path_exists",
]
