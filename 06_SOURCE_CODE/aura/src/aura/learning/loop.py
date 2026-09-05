"""Learning loop: observe -> evaluate -> signal -> validate -> apply -> monitor -> rollback.

The learning cycle is a *governed* pipeline, not a self-modification shortcut:

1. :meth:`LearningLoop.observe` records an experience (event, context, expected
   vs observed outcome).
2. :meth:`LearningLoop.evaluate_and_learn` scores the latest experiences of an
   event type, converts below-threshold outcomes into a validated
   :class:`LearningSignal`, and submits it through the canonical
   :class:`LearningEngine` (validation gate, authorization for safety-relevant
   changes, versioned registry, rollback).
3. :meth:`LearningLoop.monitor` tracks a metric after a change has been applied
   and reports a regression when the metric falls below its pre-change
   baseline, so the system can request rollback instead of silently degrading.

Learning never mutates production behavior by itself: the engine's gate refuses
safety-relevant signals without explicit authorization, and all applied changes
are versioned and reversible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura.foundation.ids import new_hex
from aura.learning.engine import LearningEngine, LearningResult
from aura.learning.models import LearningSignal


@dataclass
class Experience:
    """One observed execution that the loop can learn from."""

    id: str
    event_type: str
    context: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, float] = field(default_factory=dict)
    observed: dict[str, float] = field(default_factory=dict)
    deviations: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        context: dict[str, Any] | None = None,
        expected: dict[str, float] | None = None,
        observed: dict[str, float] | None = None,
        deviations: tuple[str, ...] = (),
    ) -> Experience:
        return cls(
            id=f"exp-{new_hex()}",
            event_type=event_type,
            context=context or {},
            expected=expected or {},
            observed=observed or {},
            deviations=deviations,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "expected": self.expected,
            "observed": self.observed,
            "deviations": list(self.deviations),
        }


class ExperienceCollector:
    """Bounded in-memory experience log per event type.

    ``max_per_type`` keeps the loop from growing without bound; when the cap is
    reached the oldest experience for that event type is dropped.
    """

    def __init__(self, *, max_per_type: int = 50) -> None:
        self.max_per_type = max_per_type
        self._experiences: dict[str, list[Experience]] = {}

    def add(self, experience: Experience) -> None:
        bucket = self._experiences.setdefault(experience.event_type, [])
        bucket.append(experience)
        if len(bucket) > self.max_per_type:
            del bucket[: len(bucket) - self.max_per_type]

    def latest(self, event_type: str, *, limit: int = 10) -> list[Experience]:
        return list(self._experiences.get(event_type, [])[-limit:])

    def count(self, event_type: str | None = None) -> int:
        if event_type is not None:
            return len(self._experiences.get(event_type, []))
        return sum(len(v) for v in self._experiences.values())
@dataclass(frozen=True, slots=True)
class OutcomeScore:
    """Normalized quality of one experience: 1.0 is a perfect outcome."""

    score: float
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"score": self.score, "reasons": list(self.reasons)}


class OutcomeEvaluator:
    """Deterministic outcome scoring.

    Evaluation starts at 1.0 and subtracts deviation penalties (0.25 each),
    then folds in expected-vs-observed metric deltas (0.4 weight, capped at
    0.5 per metric). A fully missed metric therefore costs 0.5, and combined
    with deviations it can floor the score at 0. Nothing outside the explicit
    metrics/deviations influences the score, so the loop is reproducible.
    """

    def __init__(self, *, deviation_penalty: float = 0.25, metric_delta_weight: float = 0.4) -> None:
        self.deviation_penalty = deviation_penalty
        self.metric_delta_weight = metric_delta_weight

    def score(self, experience: Experience) -> OutcomeScore:
        score = 1.0
        reasons: list[str] = []
        if experience.deviations:
            penalty = min(1.0, self.deviation_penalty * len(experience.deviations))
            score = max(0.0, score - penalty)
            reasons.append(f"{len(experience.deviations)} deviation(s) penalized")
        for metric, expected in experience.expected.items():
            observed = experience.observed.get(metric)
            if observed is None:
                continue
            delta = abs(observed - expected) / max(1e-9, abs(expected))
            capped = min(0.5, delta * self.metric_delta_weight)
            score = max(0.0, score - capped)
            reasons.append(f"metric {metric} delta {delta:.3f}")
        return OutcomeScore(score=round(score, 6), reasons=tuple(reasons))


@dataclass(frozen=True, slots=True)
class RegressionReport:
    """Outcome of a post-change monitoring window."""

    metric: str
    baseline: float
    current: float
    regressed: bool
    applied_ref: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "baseline": self.baseline,
            "current": self.current,
            "regressed": self.regressed,
            "applied_ref": self.applied_ref,
        }
class LearningLoop:
    """Governed observe-learn-monitor cycle backed by :class:`LearningEngine`."""

    def __init__(
        self,
        *,
        engine: LearningEngine | None = None,
        collector: ExperienceCollector | None = None,
        evaluator: OutcomeEvaluator | None = None,
        learn_threshold: float = 0.7,
        min_experiences: int = 1,
        regression_ratio: float = 0.8,
    ) -> None:
        self.engine = engine or LearningEngine()
        self.collector = collector or ExperienceCollector()
        self.evaluator = evaluator or OutcomeEvaluator()
        self.learn_threshold = learn_threshold
        self.min_experiences = min_experiences
        self.regression_ratio = regression_ratio
        self._metric_baseline: dict[str, float] = {}

    def observe(
        self,
        *,
        event_type: str,
        context: dict[str, Any] | None = None,
        expected: dict[str, float] | None = None,
        observed: dict[str, float] | None = None,
        deviations: tuple[str, ...] = (),
    ) -> Experience:
        """Record an experience and feed it into the learning pipeline."""
        experience = Experience.create(
            event_type=event_type,
            context=context,
            expected=expected,
            observed=observed,
            deviations=deviations,
        )
        self.collector.add(experience)
        return experience

    def evaluate_and_learn(
        self, *, event_type: str, authorized: bool = False
    ) -> LearningResult | None:
        """Score the latest experiences; submit a signal when quality is poor.

        Returns ``None`` when there is not enough evidence yet or the recent
        outcomes are acceptable. The generated signal is always non-safety-
        relevant: learning that touches safety policy must be submitted by an
        explicit caller who sets ``authorized=True`` on a crafted signal instead
        of via automated thresholds.
        """
        experiences = self.collector.latest(event_type, limit=self.min_experiences)
        if len(experiences) < self.min_experiences:
            return None
        scores = [self.evaluator.score(experience) for experience in experiences]
        average = sum(s.score for s in scores) / len(scores)
        if average >= self.learn_threshold:
            return None
        signal = LearningSignal.create(
            kind="loop_improvement",
            content=(
                f"event '{event_type}' scored {average:.3f} below threshold "
                f"{self.learn_threshold}; propose an improvement plus regression validation"
            ),
            evidence=[{"score": round(s.score, 6)} for s in scores],
        )
        signal.authorized = authorized
        return self.engine.submit(signal)

    def record_metric(self, metric: str, value: float) -> None:
        """Record a pre-change baseline for post-change regression monitoring."""
        if metric not in self._metric_baseline:
            self._metric_baseline[metric] = value

    def monitor(self, metric: str, current: float, *, applied_ref: str | None = None) -> RegressionReport:
        """Compare the current metric against its recorded baseline."""
        baseline = self._metric_baseline.get(metric)
        if baseline is None:
            return RegressionReport(
                metric=metric, baseline=current, current=current, regressed=False, applied_ref=applied_ref
            )
        regressed = baseline > 0.0 and current < baseline * self.regression_ratio
        return RegressionReport(
            metric=metric,
            baseline=baseline,
            current=current,
            regressed=regressed,
            applied_ref=applied_ref,
        )

    def rollback(self, ref: str) -> object:
        """Delegate rollback of a versioned, applied learning change."""
        return self.engine.rollback(ref)

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "experiences": self.collector.count(),
            "threshold": self.learn_threshold,
        }


__all__ = [
    "Experience",
    "ExperienceCollector",
    "LearningLoop",
    "OutcomeEvaluator",
    "OutcomeScore",
    "RegressionReport",
]