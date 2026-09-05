"""Epistemic ledger and claim passports.

The ledger is an append-only record of every claim entry with its status.
A claim passport is a per-claim dossier: origin, supporting evidence, quality,
and trust.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura.foundation.ids import ClaimId, ExecutionId
from aura.research.models import EpistemicStatus, SourceQuality


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    claim_id: ClaimId
    claim: str
    status: EpistemicStatus
    confidence: float
    evidence_count: int
    execution_id: ExecutionId
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": str(self.claim_id),
            "claim": self.claim,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "execution_id": str(self.execution_id),
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class ClaimPassport:
    claim_id: ClaimId = field(default_factory=ClaimId.new)
    claim: str = ""
    origin: str = ""
    execution_id: ExecutionId | None = None
    supporting: list[str] = field(default_factory=list)
    contradicting: list[str] = field(default_factory=list)
    trust: float = 0.0
    source_quality: SourceQuality = SourceQuality.UNKNOWN
    freshness: float = 0.5
    status: EpistemicStatus = EpistemicStatus.UNKNOWN
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": str(self.claim_id),
            "claim": self.claim,
            "origin": self.origin,
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "supporting": list(self.supporting),
            "contradicting": list(self.contradicting),
            "trust": self.trust,
            "source_quality": self.source_quality.value,
            "freshness": self.freshness,
            "status": self.status.value,
            "issued_at": self.issued_at.isoformat(),
        }


class EpistemicLedger:
    """Append-only ledger of recorded claims with their status transitions."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._passports: dict[str, ClaimPassport] = {}

    def record(
        self,
        *,
        claim: str,
        status: EpistemicStatus,
        confidence: float,
        evidence_count: int,
        execution_id: ExecutionId,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            claim_id=ClaimId.new(),
            claim=claim,
            status=status,
            confidence=confidence,
            evidence_count=evidence_count,
            execution_id=execution_id,
        )
        self._entries.append(entry)
        return entry

    def issue_passport(
        self,
        *,
        claim: str,
        origin: str,
        execution_id: ExecutionId | None,
        supporting: list[str],
        contradicting: list[str],
        trust: float,
        source_quality: SourceQuality,
        freshness: float,
    ) -> ClaimPassport:
        passport = ClaimPassport(
            claim=claim,
            origin=origin,
            execution_id=execution_id,
            supporting=supporting,
            contradicting=contradicting,
            trust=trust,
            source_quality=source_quality,
            freshness=freshness,
        )
        self._passports[str(passport.claim_id)] = passport
        return passport

    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def passport(self, claim: str) -> ClaimPassport | None:
        for candidate in self._passports.values():
            if candidate.claim == claim:
                return candidate
        return None

    def passports(self) -> list[ClaimPassport]:
        return list(self._passports.values())

    def contradictions(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        by_negation: dict[str, str] = {}
        for entry in self._entries:
            plain = (
                entry.claim.replace("does not ", "").replace("not ", "")
                if "not" in entry.claim
                else entry.claim
            )
            if entry.claim != plain and plain in by_negation:
                pairs.append((by_negation[plain], entry.claim))
            else:
                by_negation.setdefault(plain, entry.claim)
        return pairs

    def search(self, needle: str) -> list[LedgerEntry]:
        return [e for e in self._entries if needle.lower() in e.claim.lower()]


__all__ = ["ClaimPassport", "EpistemicLedger", "LedgerEntry"]