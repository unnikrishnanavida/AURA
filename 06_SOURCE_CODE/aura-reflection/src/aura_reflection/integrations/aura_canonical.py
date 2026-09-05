"""Adapter bridging aura-reflection to the canonical AURA runtime.

Converts aura-reflection requests/results into the canonical
``aura.reflection`` / ``aura.learning`` contracts, letting the standalone
reflection subsystem feed the canonical runtime through explicit boundaries.
The canonical engine is never duplicated: translation only.
"""

from __future__ import annotations

from typing import Any

from aura_reflection.bridges.learning_bridge import LearningSignal
from aura_reflection.models.reflection_request import ActionOutcome, ReflectionRequest


class BridgeUnavailable(RuntimeError):
    """The canonical aura package is not importable."""


def _canonical_models() -> Any:
    try:
        from aura.reflection import models as _models  # type: ignore[attr-defined]

        return _models
    except ImportError as exc:  # pragma: no cover - depends on env
        raise BridgeUnavailable("canonical aura package is not installed") from exc


def to_canonical_outcome(outcome: ActionOutcome) -> Any:
    """Convert an ActionOutcome into a canonical ``aura.reflection.Outcome``."""
    models = _canonical_models()
    deviation = None if outcome.actual_result == outcome.expected_result else (outcome.actual_result or "none")
    return models.Outcome(
        goal=outcome.goal,
        success=outcome.success,
        observed={"actual_result": outcome.actual_result, "error": outcome.error},
        expected={"expected_result": outcome.expected_result},
        deviations=[] if deviation is None else [deviation],
        events_summary=[],
        metrics={},
    )


def to_canonical_signal(learning_signal: LearningSignal) -> Any:
    """Convert an approved LearningSignal into a canonical
    ``aura.reflection.models.ReflectionSignal`` (kind LESSON)."""
    models = _canonical_models()
    return models.ReflectionSignal(
        kind=models.SignalKind.LESSON,
        content=learning_signal.lesson,
        confidence=learning_signal.lesson_confidence,
        recommendations=(learning_signal.proposed_action,),
    )


def to_request(canonical_outcome: Any) -> ReflectionRequest:
    """Convert a canonical Outcome back into an aura-reflection request."""
    return ReflectionRequest(
        outcome=ActionOutcome(
            action="canonical_action",
            success=bool(getattr(canonical_outcome, "success", False)),
            goal=getattr(canonical_outcome, "goal", ""),
            expected_result=str(getattr(canonical_outcome, "expected", {}) or None),
            actual_result=str(getattr(canonical_outcome, "observed", {}) or None),
            assumptions=list(getattr(canonical_outcome, "deviations", ()) or ()),
        )
    )


__all__ = [
    "BridgeUnavailable",
    "to_canonical_outcome",
    "to_canonical_signal",
    "to_request",
]