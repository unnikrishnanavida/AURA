"""Research domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from aura.foundation.ids import ExecutionId, new_hex


class ResearchState(StrEnum):
    """Lifecycle of one research task (distinct from finding epistemology).

    The two are not interchangeable: ``ResearchState`` tracks the research
    *task* (was it requested / planned / retrieved / verified / failed /
    cancelled), while :class:`EpistemicStatus` classifies each *finding*'s
    evidential strength. They must never be conflated -- e.g. a task can be
    RETRIEVED (evidence assessed) without ever being VERIFIED.
    """

    #: Research was requested but work has not begun.
    REQUESTED = "requested"
    #: The system determined what research needs to be performed.
    PLANNED = "planned"
    #: Evidence/source material was actually retrieved (here: supplied
    #: evidence was assessed by the research engine).
    RETRIEVED = "retrieved"
    #: Retrieved evidence passed the available verification rules (at least
    #: one finding reached EVIDENCE/INFERENCE). Verification is never assumed
    #: merely because retrieval succeeded.
    VERIFIED = "verified"
    #: Research could not complete successfully.
    FAILED = "failed"
    #: Research was explicitly cancelled.
    CANCELLED = "cancelled"


class EpistemicStatus(StrEnum):
    """Epistemic strength ladder used by findings and the ledger."""

    EVIDENCE = "evidence"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    SPECULATION = "speculation"
    UNKNOWN = "unknown"


class SourceQuality(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    question: str
    sub_questions: tuple[str, ...] = ()

    @classmethod
    def create(cls, question: str, sub_questions: tuple[str, ...] = ()) -> ResearchQuestion:
        if not question.strip():
            raise ValueError("research question must not be empty")
        return cls(question=question, sub_questions=sub_questions)


@dataclass(frozen=True, slots=True)
class Finding:
    claim: str
    status: EpistemicStatus
    confidence: float
    evidence_count: int
    supporting: tuple[str, ...] = ()
    contradicting: tuple[str, ...] = ()
    source_quality: SourceQuality = SourceQuality.UNKNOWN
    source_freshness: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "supporting": list(self.supporting),
            "contradicting": list(self.contradicting),
            "source_quality": self.source_quality.value,
            "source_freshness": self.source_freshness,
        }


@dataclass(frozen=True, slots=True)
class ReproducibilityCapsule:
    capsule_id: str = field(default_factory=lambda: f"cap-{new_hex()}")
    question: str = ""
    sub_questions: tuple[str, ...] = ()
    seed: int | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "question": self.question,
            "sub_questions": list(self.sub_questions),
            "seed": self.seed,
            "inputs": self.inputs,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ResearchInput:
    question: ResearchQuestion
    claims: tuple[str, ...] = ()
    evidence: dict[str, tuple[float, SourceQuality, float]] = field(default_factory=dict)
    seed: int | None = None
    execution_id: ExecutionId = field(default_factory=ExecutionId.new)

    def supports(self, claim: str) -> tuple[float, SourceQuality, float]:
        return self.evidence.get(claim, (0.0, SourceQuality.UNKNOWN, 0.3))


__all__ = [
    "EpistemicStatus",
    "Finding",
    "ReproducibilityCapsule",
    "ResearchInput",
    "ResearchQuestion",
    "ResearchState",
    "SourceQuality",
]