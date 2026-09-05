"""AURA brain.

The cognitive orchestration layer. The Brain wires memory, knowledge,
reasoning, planning, reflection, learning, the flight recorder, and
observability behind one lifecycle and propagates confidence, uncertainty,
and provenance through every stage.
"""

from __future__ import annotations

from aura.brain.engine import Brain, BrainEngine, BrainResult, StepSummary

__all__ = ["Brain", "BrainEngine", "BrainResult", "StepSummary"]