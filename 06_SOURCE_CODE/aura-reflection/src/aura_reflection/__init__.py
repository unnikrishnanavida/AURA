"""AURA Reflection — reflective intelligence over action outcomes.

Real reflective capabilities:

- execution / reasoning / outcome review
- failure & success analysis
- assumption review
- counterfactual analysis
- lesson extraction
- validated learning-signal generation

Critical safety property: reflection NEVER mutates system behavior, policies,
or memory by itself. It produces candidate ImprovementSignals that default to
unapproved; only an explicit authorization gate may approve them and only an
explicit, authorized bridge may apply them to the system.
"""

from __future__ import annotations

from aura_reflection.bridges.learning_bridge import (
    LearningSignal,
    LearningSignalBroker,
)
from aura_reflection.models.reflection_request import (
    ActionOutcome,
    OutcomeKind,
    ReflectionRequest,
)
from aura_reflection.models.reflection_result import (
    AnalysisFinding,
    Counterfactual,
    ImprovementSignal,
    Lesson,
    ReflectionResult,
    ReviewFinding,
)
from aura_reflection.services.reflection_engine import ReflectionEngine
from aura_reflection.services.reflection_gate import (
    ReflectionGate,
    UnauthorizedMutationError,
    apply_if_authorized,
)
from aura_reflection.services.reflection_orchestrator import ReflectionOrchestrator
from aura_reflection.validation.evidence_gate import EvidenceGate

__all__ = [
    "ActionOutcome",
    "AnalysisFinding",
    "Counterfactual",
    "EvidenceGate",
    "ImprovementSignal",
    "LearningSignal",
    "LearningSignalBroker",
    "Lesson",
    "OutcomeKind",
    "ReflectionEngine",
    "ReflectionGate",
    "ReflectionOrchestrator",
    "ReflectionRequest",
    "ReflectionResult",
    "ReviewFinding",
    "UnauthorizedMutationError",
    "apply_if_authorized",
]