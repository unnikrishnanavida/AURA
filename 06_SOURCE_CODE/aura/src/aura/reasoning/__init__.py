"""AURA reasoning engine.

Multi-strategy, uncertainty-first reasoning: hypotheses, assumptions,
evidence, inference, confidence, consensus, verification, and full reasoning
traces. AURA is explicitly allowed to answer "I do not know".
"""

from __future__ import annotations

from aura.reasoning.abductive import AbductiveStrategy
from aura.reasoning.analogical import AnalogicalStrategy
from aura.reasoning.calibration import CalibrationBin, CalibrationTracker
from aura.reasoning.causal import CausalStrategy
from aura.reasoning.consensus import ConsensusEngine, ConsensusVerdict
from aura.reasoning.counterfactual import CounterfactualStrategy
from aura.reasoning.deductive import DeductiveStrategy
from aura.reasoning.engine import ReasoningEngine, ReasoningInput, ReasoningResult
from aura.reasoning.models import (
    Assumption,
    Case,
    Conclusion,
    InferenceStep,
    ReasoningTrace,
    Rule,
    make_conclusion,
)
from aura.reasoning.probabilistic import BayesianStrategy
from aura.reasoning.uncertainty import UncertaintyLevel, uncertainty_from_confidence
from aura.reasoning.verification import VerificationEngine

__all__ = [
    "AbductiveStrategy",
    "AnalogicalStrategy",
    "Assumption",
    "BayesianStrategy",
    "CalibrationBin",
    "CalibrationTracker",
    "Case",
    "CausalStrategy",
    "Conclusion",
    "ConsensusEngine",
    "ConsensusVerdict",
    "CounterfactualStrategy",
    "DeductiveStrategy",
    "InferenceStep",
    "ReasoningEngine",
    "ReasoningInput",
    "ReasoningResult",
    "ReasoningTrace",
    "Rule",
    "UncertaintyLevel",
    "VerificationEngine",
    "make_conclusion",
    "uncertainty_from_confidence",
]