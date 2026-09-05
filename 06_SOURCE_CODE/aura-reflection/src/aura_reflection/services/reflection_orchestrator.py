"""Reflection orchestrator: composes the full reflective flow.

    ACTION
      -> OUTCOME
      -> REFLECTION (failure/success + assumption review)
      -> COUNTERFACTUAL ANALYSIS
      -> LESSON
      -> VALIDATED LEARNING SIGNAL (requires external authorization)

The orchestrator runs the engine, then applies the evidence gate, but it
NEVER approves signals itself. Producing an approved learning signal requires
an explicit, authorized call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura_reflection.bridges.learning_bridge import LearningSignal, LearningSignalBroker
from aura_reflection.models.reflection_request import ReflectionRequest
from aura_reflection.models.reflection_result import ReflectionResult
from aura_reflection.services.reflection_engine import ReflectionEngine
from aura_reflection.services.reflection_gate import ReflectionGate
from aura_reflection.validation.evidence_gate import EvidenceGate, ValidationResult


@dataclass
class OrchestratedReflection:
    """The result of a full orchestrated reflection pass.

    ``reflection`` is the raw engine output (signals unapproved).
    ``validation`` is the evidence-gate verdict.
    ``learning_signal`` is only populated after an explicit authorized call to
    :meth:`ReflectionOrchestrator.emit_learning_signal`.
    """

    reflection: ReflectionResult
    validation: ValidationResult = field(default_factory=ValidationResult.default)

    @property
    def approved(self) -> int:
        return len(self.reflection.approved_signals())


class ReflectionOrchestrator:
    """Runs engine + evidence gate and brokers authorized learning signals."""

    def __init__(
        self,
        engine: ReflectionEngine | None = None,
        gate: ReflectionGate | None = None,
        evidence_gate: EvidenceGate | None = None,
        broker: LearningSignalBroker | None = None,
    ) -> None:
        self.engine = engine or ReflectionEngine()
        self.gate = gate or ReflectionGate()
        self.evidence_gate = evidence_gate or EvidenceGate()
        self.broker = broker or LearningSignalBroker(gate=self.gate)

    def reflect(self, request: ReflectionRequest) -> OrchestratedReflection:
        """Run the full reflective pipeline without mutating anything."""
        result = self.engine.reflect(request)
        validation = self.evidence_gate.validate(result)
        return OrchestratedReflection(reflection=result, validation=validation)

    def emit_learning_signal(
        self,
        orchestrated: OrchestratedReflection,
        *,
        signal_index: int = 0,
        approver: str,
    ) -> LearningSignal:
        """Produce a validated learning signal from an approved signal.

        This is the ONLY path from reflection to a learning signal. It
        authorizes the candidate signal via the gate (recording who approved
        it) and packages it via the broker. It never self-approves.
        """
        candidates = orchestrated.reflection.signals
        if not candidates:
            raise ValueError("no signals to emit")
        if not (0 <= signal_index < len(candidates)):
            raise ValueError(f"signal_index {signal_index} out of range")
        approved = self.gate.authorize(candidates[signal_index], approver=approver)
        return self.broker.package(approved)