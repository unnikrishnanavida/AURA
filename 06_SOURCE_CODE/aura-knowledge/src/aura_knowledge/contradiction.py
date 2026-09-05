"""Contradiction detection for aura-knowledge.

Contradictions arise when two claims target the same predicate with opposing
polarity, or when a single claim carries both supporting and contradicting
evidence. Contradictory evidence must remain visible: the engine never hides
conflicting support behind a single aggregate score.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from aura_knowledge.core.models import Claim, Evidence, VerificationStatus

_NEGATIONS = ("not ", "no ", "never ", "cannot ", "false ", "un-", "dis-", "refuses ")


def _is_negated(statement: str) -> bool:
    lowered = statement.lower()
    return any(token in lowered or lowered.startswith(token) for token in _NEGATIONS)


@dataclass(frozen=True)
class Contradiction:
    """A detected conflict between two claims (or within a single claim)."""

    first_claim_id: str
    second_claim_id: str
    basis: str
    first_statement: str
    second_statement: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Contradiction):
            return (
                (self.first_claim_id, self.second_claim_id)
                == (other.first_claim_id, other.second_claim_id)
                and self.basis == other.basis
            )
        if isinstance(other, tuple) and len(other) == 2:
            # Support membership checks like ``(claim_id, statement) in
            # contradictions()``.
            if other[0] == self.first_claim_id:
                return other[1] == self.first_statement
            if other[0] == self.second_claim_id:
                return other[1] == self.second_statement
            return False
        return NotImplemented

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_claim_id": self.first_claim_id,
            "second_claim_id": self.second_claim_id,
            "basis": self.basis,
            "first_statement": self.first_statement,
            "second_statement": self.second_statement,
        }


class ContradictionDetector:
    """Detects conflicting claims and internally conflicting evidence."""

    def detect_claims(self, claims: Iterable[Claim]) -> list[Contradiction]:
        """Find pairs of claims with the same predicate and opposing polarity."""
        claims = list(claims)
        found: list[Contradiction] = []
        seen: set[tuple[str, str]] = set()
        for i, left in enumerate(claims):
            for right in claims[i + 1 :]:
                if not left.predicate or left.predicate != right.predicate:
                    continue
                if left.verification is VerificationStatus.REFUTED and right.verification is VerificationStatus.REFUTED:
                    continue
                neg_left = _is_negated(left.statement)
                neg_right = _is_negated(right.statement)
                if neg_left != neg_right:
                    pair = _ordered_pair(left.claim_id, right.claim_id)
                    if pair not in seen:
                        seen.add(pair)
                        found.append(
                            Contradiction(
                                first_claim_id=left.claim_id,
                                second_claim_id=right.claim_id,
                                basis=f"predicate {left.predicate!r} with opposing polarity",
                                first_statement=left.statement,
                                second_statement=right.statement,
                            )
                        )
        return found

    def internal_conflict(self, claim: Claim) -> Contradiction | None:
        """Return a contradiction when a claim carries both support and
        contradicting evidence."""
        if not self.has_internal_conflict(claim.evidence):
            return None
        return Contradiction(
            first_claim_id=claim.claim_id,
            second_claim_id=claim.claim_id,
            basis="claim carries both supporting and contradicting evidence",
            first_statement=claim.statement,
            second_statement="(internal evidence conflict)",
        )

    def has_internal_conflict(self, evidence: Iterable[Evidence]) -> bool:
        """True when a claim carries both supporting and contradicting evidence."""
        evidence = list(evidence)
        supports = [e for e in evidence if e.support > 0]
        contradicts = [e for e in evidence if e.support < 0]
        return bool(supports and contradicts)

    def contradiction_for_claim(self, claim: Claim, claims: Iterable[Claim]) -> Contradiction | None:
        """Return the first contradiction involving the given claim."""
        internal = self.internal_conflict(claim)
        if internal is not None:
            return internal
        for conflict in self.detect_claims(claims):
            if claim.claim_id in (conflict.first_claim_id, conflict.second_claim_id):
                return conflict
        return None


def _ordered_pair(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)


__all__ = ["Contradiction", "ContradictionDetector"]