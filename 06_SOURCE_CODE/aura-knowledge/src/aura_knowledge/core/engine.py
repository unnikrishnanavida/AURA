"""Knowledge engine for aura-knowledge.

The engine owns the claim/evidence/source lifecycle and enforces the core
epistemic invariants:

- Unsupported claims must not become verified knowledge.
- Contradictory evidence must remain visible and blocks verification.
- Provenance must never be silently lost.
- Freshness is represented explicitly.
- Confidence and verification are distinct.
- Uncertainty is first-class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from aura_knowledge.contradiction import Contradiction, ContradictionDetector
from aura_knowledge.core.errors import (
    ClaimNotFoundError,
    SourceNotFoundError,
    ValidationError,
)
from aura_knowledge.core.models import (
    Claim,
    ClaimStatus,
    Evidence,
    KnowledgeResult,
    Provenance,
    Source,
    VerificationStatus,
)
from aura_knowledge.freshness import FreshnessEngine
from aura_knowledge.fusion import EvidenceFusion
from aura_knowledge.trust import TrustModel

_CONFLICT_UNCERTAINTY_THRESHOLD = 0.5


@dataclass
class KnowledgeEngine:
    """An in-memory knowledge base with verification, trust, and revision."""

    verification_threshold: float = 0.7
    freshness_ttl: timedelta | None = None
    freshness_half_life_days: float = 30.0
    claims: dict[str, Claim] = field(default_factory=dict)
    sources: dict[str, Source] = field(default_factory=dict)
    fusion: EvidenceFusion = field(default_factory=EvidenceFusion)
    detector: ContradictionDetector = field(default_factory=ContradictionDetector)
    trust: TrustModel = field(default_factory=TrustModel)
    _now: datetime | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not 0.0 <= self.verification_threshold <= 1.0:
            raise ValidationError("verification_threshold must be in [0,1]")
        self.trust.freshness_half_life_days = self.freshness_half_life_days
        self._freshness = FreshnessEngine(ttl=self.freshness_ttl, now=self._now)

# ------------------------------------------------------------------
    # claims
    # ------------------------------------------------------------------
    def add_claim(
        self,
        statement: str,
        *,
        predicate: tuple[str, ...] = (),
        created_by: str = "unknown",
    ) -> Claim:
        if not statement or not statement.strip():
            raise ValidationError("claim statement must not be empty")
        claim = Claim(
            statement=statement,
            predicate=tuple(predicate),
            created_at=self.now(),
        )
        claim.provenance = Provenance(
            claim_id=claim.claim_id,
            created_by=created_by,
            created_at=claim.created_at,
        )
        self.claims[claim.claim_id] = claim
        return claim

    def get_claim(self, claim_id: str) -> Claim:
        if claim_id not in self.claims:
            raise ClaimNotFoundError(f"claim not found: {claim_id}")
        return self.claims[claim_id]

    # ------------------------------------------------------------------
    # sources
    # ------------------------------------------------------------------
    def register_source(self, source: Source) -> Source:
        self.sources[source.identifier] = source
        return source

    def get_source(self, identifier: str) -> Source:
        if identifier not in self.sources:
            raise SourceNotFoundError(f"source not found: {identifier}")
        return self.sources[identifier]

    def update_source_reputation(self, identifier: str, *, verified: bool) -> float:
        """Update a source's reputation based on verification outcomes.

        Confirmed sources rise; contradicted/refuted sources fall.
        """
        source = self.get_source(identifier)
        delta = 0.1 if verified else -0.2
        updated = round(max(0.0, min(1.0, source.reputation + delta)), 6)
        self.sources[identifier] = Source(
            identifier=source.identifier,
            kind=source.kind,
            reputation=updated,
            metadata={**source.metadata, "previous_reputation": source.reputation},
        )
        return updated
    def now(self) -> datetime:
        return self._now or datetime.now(UTC)
# ------------------------------------------------------------------
    # evidence
    # ------------------------------------------------------------------
    def add_evidence(self, claim_id: str, evidence: Evidence) -> Evidence:
        """Attach evidence to a claim, updating provenance/confidence/status."""
        claim = self.get_claim(claim_id)
        claim.evidence.append(evidence)
        self._refresh_provenance(claim)
        self._refuse_duplicate(claim, evidence)
        self._reassess(claim)
        return evidence

    def _refresh_provenance(self, claim: Claim) -> None:
        if claim.provenance is None:
            return
        evidence_ids = [*claim.provenance.evidence_ids, *[e.evidence_id for e in claim.evidence]]
        source_ids = [*claim.provenance.source_ids, *[e.source.identifier for e in claim.evidence]]
        claim.provenance = Provenance(
            claim_id=claim.provenance.claim_id,
            evidence_ids=tuple(dict.fromkeys(evidence_ids)),
            source_ids=tuple(dict.fromkeys(source_ids)),
            created_by=claim.provenance.created_by,
            created_at=claim.provenance.created_at,
            details=claim.provenance.details,
        )

    def _refuse_duplicate(self, claim: Claim, evidence: Evidence) -> None:
        seen: set[str] = set()
        kept: list[Evidence] = []
        for ev in [*claim.evidence]:
            if ev.evidence_id in seen:
                continue
            seen.add(ev.evidence_id)
            kept.append(ev)
        claim.evidence = kept

    def _reset_unverified(self, claim: Claim) -> None:
        """Reset verification to UNVERIFIED unless it is in a terminal state.

        REFUTED and CONTESTED are terminal and must never be silently
        overwritten by reassessment.
        """
        if claim.verification not in (VerificationStatus.REFUTED, VerificationStatus.CONTESTED):
            claim.verification = VerificationStatus.UNVERIFIED

    def _reassess(self, claim: Claim) -> None:
        """Recompute confidence and knowledge status after evidence changes.

        This deliberately does NOT auto-promote to VERIFIED: verification is
        an explicit lifecycle step. Disqualifying conditions (conflict, no
        evidence, staleness, high uncertainty, low confidence) reset
        verification to UNVERIFIED.
        """
        claim.confidence = self.fusion.fuse(claim.evidence)
        self._freshness.apply_freshness(claim)
        if claim.status is ClaimStatus.OUTDATED:
            self._reset_unverified(claim)
            return
        if self.detector.internal_conflict(claim) is not None:
            claim.status = ClaimStatus.CONTRADICTORY
            self._reset_unverified(claim)
            return
        if not claim.evidence:
            claim.status = ClaimStatus.UNSUPPORTED
            self._reset_unverified(claim)
            return
        if claim.confidence.uncertainty >= _CONFLICT_UNCERTAINTY_THRESHOLD:
            claim.status = ClaimStatus.UNCERTAIN
            self._reset_unverified(claim)
            return
        if claim.confidence.value >= self.verification_threshold:
            claim.status = ClaimStatus.SUPPORTED
        elif claim.confidence.value < 0.5:
            claim.status = ClaimStatus.UNSUPPORTED
            self._reset_unverified(claim)
        else:
            claim.status = ClaimStatus.UNCERTAIN
            self._reset_unverified(claim)
# ------------------------------------------------------------------
    # verification
    # ------------------------------------------------------------------
    def verify(self, claim_id: str) -> VerificationStatus:
        """Run verification on a claim.

        Verification is the explicit promotion step: only claims with adequate,
        unambiguous, fresh evidence may become VERIFIED. Claims with no
        evidence, conflicting evidence, staleness, high uncertainty, or
        insufficient confidence remain UNVERIFIED.
        """
        claim = self.get_claim(claim_id)
        self._reassess(claim)
        if self._verify_qualifies(claim):
            claim.verification = VerificationStatus.VERIFIED
        else:
            # do not clobber terminal states (REFUTED / CONTESTED)
            self._reset_unverified(claim)
        return claim.verification

    def _verify_qualifies(self, claim: Claim) -> bool:
        if not claim.evidence:
            return False
        # Refutation and contestation are terminal until explicitly revised.
        if claim.verification in (VerificationStatus.REFUTED, VerificationStatus.CONTESTED):
            return False
        if claim.status in (ClaimStatus.OUTDATED, ClaimStatus.CONTRADICTORY):
            return False
        if claim.confidence is None:
            return False
        if claim.confidence.uncertainty >= _CONFLICT_UNCERTAINTY_THRESHOLD:
            return False
        return claim.confidence.value >= self.verification_threshold

    def refute(self, claim_id: str, *, reason: str = "") -> Claim:
        """Mark a claim refuted (opposite was verified)."""
        claim = self.get_claim(claim_id)
        claim.verification = VerificationStatus.REFUTED
        claim.status = ClaimStatus.UNSUPPORTED
        claim.metadata["refuted_at"] = self.now()
        claim.metadata["refutation_reason"] = reason
        return claim

    # ------------------------------------------------------------------
    # retrieval
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str = "",
        *,
        predicate: tuple[str, ...] = (),
        limit: int = 10,
        verified_only: bool = False,
    ) -> list[KnowledgeResult]:
        """Retrieve claims matching the query, ranked by trust.

        Verified claims always rank above unverified ones. Results carry an
        explicit ``known``/``says_unknown`` signal so 'I do not know' is
        first-class rather than an absence of a hit.
        """
        candidates = list(self.claims.values())
        if predicate:
            candidates = [c for c in candidates if c.predicate == tuple(predicate)]
        if query:
            needle = query.lower()
            candidates = [c for c in candidates if needle in c.statement.lower()]
        if verified_only:
            candidates = [c for c in candidates if c.verification is VerificationStatus.VERIFIED]

        def rank_key(claim: Claim) -> tuple[int, float]:
            verified_rank = 0 if claim.verification is VerificationStatus.VERIFIED else 1
            return (verified_rank, -self.trust.assess(claim, now=self.now())["trust"])

        ranked = sorted(candidates, key=rank_key)
        return [
            KnowledgeResult(claim=claim, trust=self.trust.assess(claim, now=self.now())["trust"])
            for claim in ranked[:limit]
        ]

    # ------------------------------------------------------------------
    # contradictions
    # ------------------------------------------------------------------
    def contradictions(self) -> list[Contradiction]:
        """Return all visible contradictions (inter-claim and intra-claim)."""
        found: list[Contradiction] = []
        found.extend(self.detector.detect_claims(self.claims.values()))
        for claim in self.claims.values():
            internal = self.detector.internal_conflict(claim)
            if internal is not None:
                found.append(internal)
        return found

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------
    def count(self) -> int:
        return len(self.claims)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "claims": self.count(),
            "sources": len(self.sources),
            "contradictions": len(self.contradictions()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "claims": [c.to_dict() for c in self.claims.values()],
            "contradictions": [c.to_dict() for c in self.contradictions()],
        }


__all__ = ["KnowledgeEngine"]
