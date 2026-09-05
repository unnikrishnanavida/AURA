"""Reasoning calibration.

Tracks the relationship between *predicted* confidence and *actual* outcome
quality so reasoning quality is measurable instead of asserted. The evaluator
bins predictions by confidence bracket and reports the mean absolute
calibration error (ACE) over each bin: 0.0 means predictions exactly matched
outcomes, 0.5 means a total disconnect.

Calibration is deterministic and offline: recording and evaluation never
influence the reasoning engine itself.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """Statistics for one confidence bracket."""

    lower: float
    upper: float
    predictions: int = 0
    average_confidence: float = 0.0
    average_outcome: float = 0.0

    @property
    def error(self) -> float:
        """Mean absolute difference between predicted and realized quality."""
        if self.predictions == 0:
            return 0.0
        return round(abs(self.average_confidence - self.average_outcome), 6)

    def to_dict(self) -> dict[str, object]:
        return {
            "bin": f"[{self.lower:.3f},{self.upper:.3f})",
            "predictions": self.predictions,
            "average_confidence": self.average_confidence,
            "average_outcome": self.average_outcome,
            "error": self.error,
        }


class CalibrationTracker:
    """Record (confidence, outcome) pairs and evaluate calibration quality.

    ``outcome`` must be 1.0 when the prediction was correct and 0.0 otherwise.
    The tracker never mutates the caller's objects.
    """

    def __init__(self, *, bins: tuple[tuple[float, float], ...] = (
        (0.0, 0.4),
        (0.4, 0.7),
        (0.7, 1.001),
    )) -> None:
        if not bins:
            raise ValueError("at least one confidence bin is required")
        self._bins = bins
        self._records: list[tuple[float, float]] = []

    def record(self, *, confidence: float, outcome: float) -> None:
        """Log one prediction. Confidence/outcome are clamped to [0,1]."""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {confidence}")
        if outcome not in (0.0, 1.0):
            raise ValueError(f"outcome must be 0.0 or 1.0, got {outcome}")
        self._records.append((min(1.0, max(0.0, confidence)), outcome))

    def bins(self) -> list[CalibrationBin]:
        """Aggregate recorded pairs into confidence brackets."""
        aggregated: list[CalibrationBin] = []
        for lower, upper in self._bins:
            pairs = [p for p in self._records if lower <= p[0] < upper]
            count = len(pairs)
            if count == 0:
                aggregated.append(CalibrationBin(lower=lower, upper=upper))
                continue
            avg_confidence = sum(p[0] for p in pairs) / count
            avg_outcome = sum(p[1] for p in pairs) / count
            aggregated.append(
                CalibrationBin(
                    lower=lower,
                    upper=upper,
                    predictions=count,
                    average_confidence=round(avg_confidence, 6),
                    average_outcome=round(avg_outcome, 6),
                )
            )
        return aggregated

    def mean_absolute_error(self) -> float:
        """Overall calibration error weighted by prediction count per bin."""
        total_predictions = len(self._records)
        if total_predictions == 0:
            return 0.0
        weighted = sum(bin_.predictions * bin_.error for bin_ in self.bins())
        return round(weighted / total_predictions, 6)

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict[str, object]:
        return {
            "predictions": self.count(),
            "mean_absolute_error": self.mean_absolute_error(),
            "bins": [b.to_dict() for b in self.bins()],
        }


__all__ = ["CalibrationBin", "CalibrationTracker"]