"""Knowledge domain models.

A Claim is a proposition. Evidence is what supports it. A Source has a
reliability rating. Verification tracks whether the claim has been checked.
This separation is what makes AURA knowledge trustworthy rather than a bag of
strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from aura.foundation.ids import ClaimId
from aura.memory.models import Provenance


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REFUTED = "refuted"
    CONTESTED = "contested"


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    reliability: float = 0.5
    kind: str = "document"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError(f"source reliability must be in [0,1], got {self.reliability}")


@dataclass(frozen=True, slots=True)
class Evidence:
    content: str
    source: Source
    quality: float = 0.5
    collected_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError(f"evidence quality must be in [0,1], got {self.quality}")


@dataclass
class Claim:
    id: ClaimId
    statement: str
    predicate: tuple[str, ...] = ()
    evidence: list[Evidence] = field(default_factory=list)
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = 0.0
    provenance: Provenance = field(default_factory=lambda: Provenance(source="unknown"))
    created_at: datetime | None = None
    contradicts: tuple[str, ...] = ()

    @classmethod
    def create(cls, *, statement: str, predicate: tuple[str, ...] = (), claim_id: ClaimId | None = None) -> Claim:
        return cls(id=claim_id or ClaimId.new(), statement=statement, predicate=predicate)

    def with_evidence(self, evidence: Evidence, *, weight: float = 0.2) -> Claim:
        self.evidence.append(evidence)
        total = sum(e.quality * e.source.reliability for e in self.evidence)
        self.confidence = min(1.0, total * weight * len(self.evidence))
        return self


@dataclass(frozen=True)
class KnowledgeResult:
    claim: Claim

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": str(self.claim.id),
            "statement": self.claim.statement,
            "status": self.claim.status.value,
            "confidence": self.claim.confidence,
        }


__all__ = ["Claim", "Evidence", "KnowledgeResult", "Source", "VerificationStatus"]