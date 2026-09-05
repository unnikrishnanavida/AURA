"""Contradiction detection.

Finds pairs of claims with overlapping predicates and opposite evaluations, so
the knowledge base can flag CONFLICTS instead of silently trusting both.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aura.knowledge.models import Claim

_NEGATIONS = ("not ", "no ", "never ", "cannot ", "false ", "un-", "dis-")


@dataclass(frozen=True)
class Contradiction:
    first: Claim
    second: Claim
    basis: str


def _is_negated(statement: str) -> bool:
    lowered = statement.lower()
    return any(lowered.startswith(token) or f" {token.strip()}" in lowered for token in _NEGATIONS)


class ContradictionDetector:
    def detect(self, claims: Iterable[Claim]) -> list[Contradiction]:
        claims = list(claims)
        found: list[Contradiction] = []
        seen: set[tuple[str, str]] = set()
        for i, left in enumerate(claims):
            for right in claims[i + 1 :]:
                if not left.predicate or left.predicate != right.predicate:
                    continue
                if left.status.value == "refuted" and right.status.value == "refuted":
                    continue
                negated_left = _is_negated(left.statement)
                negated_right = _is_negated(right.statement)
                if negated_left != negated_right:
                    left_key = str(left.id)
                    right_key = str(right.id)
                    pair = (left_key, right_key) if left_key <= right_key else (right_key, left_key)
                    if pair not in seen:
                        seen.add(pair)
                        found.append(
                            Contradiction(
                                first=left,
                                second=right,
                                basis=f"predicate {left.predicate!r} with opposing polarity",
                            )
                        )
        return found


__all__ = ["Contradiction", "ContradictionDetector"]