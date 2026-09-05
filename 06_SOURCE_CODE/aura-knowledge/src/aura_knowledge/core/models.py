"""Domain models for aura-knowledge.

The conceptual model implements the required pipeline:

    CLAIM
      -> EVIDENCE
      -> SOURCE
      -> PROVENANCE
      -> VERIFICATION
      -> CONFIDENCE + UNCERTAINTY
      -> KNOWLEDGE STATE

Knowledge states are: supported, unsupported, uncertain, contradictory,
outdated, unverified; verification is tracked separately from confidence.
Uncertainty is first-class.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


def _new_id(prefix: str, entropy: int = 8) -> str:
    return f"{prefix}-{uuid.uuid4().hex[: entropy * 2]}"


def new_claim_id() -> str:
    return _new_id("cl")


def new_evidence_id() -> str:
    return _new_id("ev")


def new_source_id() -> str:
    return _new_id("src")


class ClaimStatus(StrEnum):
    """Holistic knowledge state of a claim."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNCERTAIN = "uncertain"
    CONTRADICTORY = "contradictory"
    OUTDATED = "outdated"
    UNVERIFIED = "unverified"


class VerificationStatus(StrEnum):
    """Whether the claim has been checked through verification.

    This is deliberately distinct from ClaimStatus and from
    confidence: a claim can be highly confident yet unverified; a verified
    claim can still be outdated or refuted.
    """

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REFUTED = "refuted"
    CONTESTED = "contested"


class SourceKind(StrEnum):
    DOCUMENT = "document"
    EXPERIMENT = "experiment"
    OBSERVATION = "observation"
    REPORT = "report"
    MODEL = "model"
    OTHER = "other"


class EvidenceMode(StrEnum):
    SUPPORT = "support"
    CONTRADICT = "contradict"


@dataclass(frozen=True, slots=True)
class Source:
    """An origin of evidence with an explicit reliability/reputation score."""

    identifier: str
    kind: str = SourceKind.OTHER.value
    reputation: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.reputation <= 1.0:
            raise ValueError(f"source reputation must be in [0,1], got {self.reputation}")
        if not self.identifier.strip():
            raise ValueError("source identifier must not be empty")


@dataclass(frozen=True, slots=True)
class Evidence:
    """A single piece of evidence with direction (support/contradict)."""

    content: str
    support: float  # in [-1, 1]; positive supports, negative contradicts
    reliability: float = 0.5  # intrinsic reliability of the evidence itself
    source: Source = field(default_factory=lambda: Source(identifier="unknown"))
    evidence_id: str = field(default_factory=new_evidence_id)
    captured_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not -1.0 <= self.support <= 1.0:
            raise ValueError(f"evidence support must be in [-1,1], got {self.support}")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError(f"evidence reliability must be in [0,1], got {self.reliability}")

    @property
    def mode(self) -> EvidenceMode:
        return EvidenceMode.SUPPORT if self.support >= 0 else EvidenceMode.CONTRADICT


@dataclass(frozen=True, slots=True)
class Confidence:
    """First-class confidence: value plus explicit uncertainty."""

    value: float
    uncertainty: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"confidence value must be in [0,1], got {self.value}")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError(f"uncertainty must be in [0,1], got {self.uncertainty}")

    def __bool__(self) -> bool:
        return self.value > 0.0

    def __repr__(self) -> str:
        return f"Confidence(value={self.value:.3f}, uncertainty={self.uncertainty:.3f})"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Immutable record of where a claim and its evidence came from.

    Provenance must never be silently lost: it is required on claim creation
    and accumulates evidence/source ids as evidence is attached.
    """

    claim_id: str
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    created_by: str = "unknown"
    created_at: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    """A proposition with its evidence, provenance, status, and confidence."""

    statement: str
    claim_id: str = field(default_factory=new_claim_id)
    predicate: tuple[str, ...] = ()
    evidence: list[Evidence] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: Confidence | None = None
    provenance: Provenance | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise ValueError("claim statement must not be empty")

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "predicate": list(self.predicate),
            "status": self.status.value,
            "verification": self.verification.value,
            "confidence": None if self.confidence is None else self.confidence.value,
            "uncertainty": None if self.confidence is None else self.confidence.uncertainty,
            "evidence_count": len(self.evidence),
            "source_ids": list(self.provenance.source_ids) if self.provenance else [],
        }


@dataclass(frozen=True, slots=True)
class KnowledgeResult:
    """Structured result of a retrieval/query, preserving uncertainty."""

    claim: Claim
    trust: float = 0.0

    @property
    def claim_id(self) -> str:
        return self.claim.claim_id

    @property
    def statement(self) -> str:
        return self.claim.statement

    @property
    def known(self) -> bool:
        """Whether this result can be treated as actionable knowledge.

        Unsupported claims must not become verified knowledge: a result is
        known only when it is verified and not outdated/contradicted.
        """
        return (
            self.claim.verification is VerificationStatus.VERIFIED
            and self.claim.status in (ClaimStatus.SUPPORTED, ClaimStatus.UNCERTAIN)
        )

    @property
    def says_unknown(self) -> bool:
        """AURA's first-class 'I do not know' representation."""
        return not self.known

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "status": self.claim.status.value,
            "verification": self.claim.verification.value,
            "confidence": None if self.claim.confidence is None else self.claim.confidence.value,
            "uncertainty": None if self.claim.confidence is None else self.claim.confidence.uncertainty,
            "trust": self.trust,
            "known": self.known,
        }


__all__ = [
    "Claim",
    "ClaimStatus",
    "Confidence",
    "Evidence",
    "EvidenceMode",
    "KnowledgeResult",
    "Provenance",
    "Source",
    "SourceKind",
    "VerificationStatus",
    "new_claim_id",
    "new_evidence_id",
    "new_source_id",
]
