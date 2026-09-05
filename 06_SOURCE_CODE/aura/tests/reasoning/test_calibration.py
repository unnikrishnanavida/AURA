"""Reasoning calibration tests: confidence-vs-outcome tracking, binning, calibration error."""

from __future__ import annotations

import pytest

from aura.reasoning.calibration import CalibrationTracker


def test_well_calibrated_low_error() -> None:
    tracker = CalibrationTracker()
    # 90% predicted -> 9 correct in 10 outcomes
    for i in range(10):
        tracker.record(confidence=0.9, outcome=1.0 if i < 9 else 0.0)
    assert tracker.mean_absolute_error() == pytest.approx(0.0, abs=1e-6)


def test_miscalibrated_high_error() -> None:
    tracker = CalibrationTracker()
    for _ in range(10):
        tracker.record(confidence=0.9, outcome=0.0)
    bins = {b.lower: b for b in tracker.bins()}
    high = bins[0.7]
    assert high.predictions == 10
    assert high.error == pytest.approx(0.9, abs=1e-6)


def test_empty_tracker_has_zero_error() -> None:
    tracker = CalibrationTracker()
    assert tracker.count() == 0
    assert tracker.mean_absolute_error() == 0.0
    assert tracker.summary()["predictions"] == 0


def test_validation_rejects_out_of_range() -> None:
    tracker = CalibrationTracker()
    with pytest.raises(ValueError):
        tracker.record(confidence=1.5, outcome=1.0)
    with pytest.raises(ValueError):
        tracker.record(confidence=0.5, outcome=0.5)


def test_bins_require_at_least_one() -> None:
    with pytest.raises(ValueError):
        CalibrationTracker(bins=())


def test_weighted_error_across_bins() -> None:
    tracker = CalibrationTracker()
    # perfect high bin dominates the weight
    for _ in range(10):
        tracker.record(confidence=0.8, outcome=1.0)
    # bad low bin is a single sample
    tracker.record(confidence=0.2, outcome=1.0)
    assert 0.0 < tracker.mean_absolute_error() < 0.5