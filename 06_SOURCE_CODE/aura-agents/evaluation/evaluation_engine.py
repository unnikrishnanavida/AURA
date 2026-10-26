"""Evaluation engine: expected state vs observed state.

The evaluation engine never accepts "the function returned without throwing"
as success. It compares *explicit* expected world-state values against
*observed* world-state values and produces a verdict. Goal progress is the
fraction of expectations matched.
"""

from __future__ import annotations

from aura_agent.evaluation.models import (
    EvaluationResult,
    EvaluationVerdict,
    StateExpectation,
)

__all__ = ["EvaluationEngine", "resolve_path", "path_exists"]


def resolve_path(path: str, state: dict):
    """Resolve a dotted path through nested dictionaries."""
    cur: object = state
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def path_exists(path: str, state: dict) -> bool:
    cur: object = state
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False
    return True


class EvaluationEngine:
    """Deterministic expected-vs-observed evaluation."""

    def evaluate(
        self,
        expectations: list[StateExpectation],
        observed_state: dict,
        *,
        goal_completed: bool = False,
    ) -> EvaluationResult:
        mismatches: list[str] = []
        matched: list[str] = []
        for exp in expectations:
            if exp.expected is None:
                if path_exists(exp.path, observed_state):
                    matched.append(exp.path)
                else:
                    mismatches.append(f"{exp.path} missing")
                continue
            value = resolve_path(exp.path, observed_state)
            if value == exp.expected:
                matched.append(exp.path)
            else:
                mismatches.append(
                    f"{exp.path}: expected {exp.expected!r}, observed {value!r}"
                )

        total = len(expectations)
        progress = (len(matched) / total) if total else 0.0

        if not mismatches:
            verdict = EvaluationVerdict.SUCCESS
        elif len(matched) == 0:
            verdict = EvaluationVerdict.FAILURE
        elif any("observed" in m for m in mismatches):
            verdict = EvaluationVerdict.STATE_MISMATCH
        else:
            verdict = EvaluationVerdict.PARTIAL

        return EvaluationResult(
            verdict=verdict,
            expectations=expectations,
            mismatches=mismatches,
            matched=matched,
            goal_progress=progress,
            goal_completed=bool(goal_completed) and not mismatches,
        )
