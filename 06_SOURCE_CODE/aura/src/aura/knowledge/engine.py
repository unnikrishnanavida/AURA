"""Knowledge base engine.

Stores claims, evidence, and sources; verifies claims against evidence;
flags contradictions; and retrieves knowledge ranked by trust.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.errors import NotFoundError
from aura.foundation.ids import ClaimId
from aura.knowledge.contradictions import Contradiction, ContradictionDetector
from aura.knowledge.models import Claim, VerificationStatus
from aura.knowledge.trust import TrustModel


@dataclass
class KnowledgeBase:
    claims: dict[str, Claim] = field(default_factory=dict)
    trust: TrustModel = field(default_factory=TrustModel)
    detector: ContradictionDetector = field(default_factory=ContradictionDetector)
    _clock: Clock = field(default_factory=SystemClock, repr=False)

    def add(self, claim: Claim) -> Claim:
        self.claims[str(claim.id)] = claim
        self._flag_contradictions(claim)
        return claim

    def get(self, claim_id: ClaimId) -> Claim:
        if str(claim_id) not in self.claims:
            raise NotFoundError(f"claim not found: {claim_id}")
        return self.claims[str(claim_id)]

    def verify(self, claim_id: ClaimId, *, require_evidence: bool = True) -> VerificationStatus:
        claim = self.get(claim_id)
        if not claim.evidence and require_evidence:
            claim.status = VerificationStatus.UNVERIFIED
        else:
            claim.status = VerificationStatus.VERIFIED
        return claim.status

    def retrieve(
        self,
        *,
        predicate: tuple[str, ...] = (),
        statement: str = "",
        limit: int = 10,
    ) -> list[tuple[Claim, dict[str, float]]]:
        candidates = list(self.claims.values())
        if predicate:
            candidates = [c for c in candidates if c.predicate == predicate]
        if statement:
            needle = statement.lower()
            candidates = [c for c in candidates if needle in c.statement.lower()]
        ranked = sorted(
            candidates,
            key=lambda c: self.trust.assess(c, now=self._clock.now())["trust"],
            reverse=True,
        )
        return [(claim, self.trust.assess(claim, now=self._clock.now())) for claim in ranked[:limit]]

    def contradictions(self) -> list[Contradiction]:
        return self.detector.detect(self.claims.values())

    def _flag_contradictions(self, claim: Claim) -> None:
        others = [v for k, v in self.claims.items() if v is not claim]
        for conflict in self.detector.detect([claim, *others]):
            other = conflict.second if str(conflict.first.id) == str(claim.id) else conflict.first
            claim.contradicts = tuple({*claim.contradicts, str(other.id)})
            claim.status = VerificationStatus.CONTESTED
            other.status = VerificationStatus.CONTESTED
            other.contradicts = tuple({*other.contradicts, str(claim.id)})

    def count(self) -> int:
        return len(self.claims)

    def health(self) -> dict[str, object]:
        return {"status": "ok", "claims": self.count()}


__all__ = ["KnowledgeBase"]