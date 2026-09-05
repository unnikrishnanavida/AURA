"""AURA reflection engine.

Analyzes outcomes, decisions, plans, execution, failures, efficiency, and
deviations; produces structured reflection signals and counterfactual reviews.
Reflection never mutates safety-critical systems directly.
"""

from __future__ import annotations

from aura.reflection.engine import ReflectionEngine, ReflectionReport
from aura.reflection.models import Outcome, ReflectionSignal, SignalKind

__all__ = ["Outcome", "ReflectionEngine", "ReflectionReport", "ReflectionSignal", "SignalKind"]