"""Grounded answering.

When the deterministic strategies decline to answer ("I do not know"), AURA may
still answer **from retrieved context** -- but only extractively, and only from
items that clear an explicit belief floor.

This is deliberately *not* a text generator. It quotes what was retrieved,
names where it came from, and carries the retrieved confidence through. It runs
before any provider generation because stored evidence is cheaper and more
traceable than an unverified generation.
"""

from __future__ import annotations

from aura.reasoning.models import Conclusion, GroundingItem, make_conclusion
from aura.reasoning.uncertainty import UncertaintyLevel, uncertainty_from_confidence

#: An item may ground an answer only when confidence x relevance clears this
#: floor. Below it the item stays visible in the context block (attribution)
#: but is not strong enough to speak for AURA. The floor is deliberately below
#: what a default-confidence (0.5) well-matched record produces, and well above
#: what a weakly-matched one does -- relevance is enforced by the assembler's
#: overlap gate, so this floor only has to separate "well matched" from
#: "barely matched".
MIN_GROUNDING_BELIEF = 0.20

_LEAD = {
    "memory": "From what you've saved",
    "knowledge": "From stored knowledge",
}


def groundable_items(items: tuple[GroundingItem, ...]) -> tuple[GroundingItem, ...]:
    """Items strong enough to ground an answer, strongest first."""
    ranked = sorted(items, key=lambda item: item.belief(), reverse=True)
    return tuple(item for item in ranked if item.belief() >= MIN_GROUNDING_BELIEF)


def build_grounded_conclusion(
    *,
    items: tuple[GroundingItem, ...],
    contradictions: tuple[tuple[str, str], ...] = (),
) -> Conclusion | None:
    """Compose an attributed, extractive answer from retrieved context.

    Returns ``None`` when nothing clears :data:`MIN_GROUNDING_BELIEF`, so the
    caller keeps its honest abstention. Contradictions are surfaced, never
    silently resolved: conflicting context yields a ``CONTESTED`` conclusion
    with zero confidence rather than a confident answer.
    """
    candidates = groundable_items(items)
    if not candidates:
        return None

    top = candidates[0]
    conflict = any(top.reference in pair for pair in contradictions)

    if conflict:
        opposing = [
            item.text
            for item in candidates[1:]
            if item.reference != top.reference
            and item.reference in {ref for pair in contradictions for ref in pair}
        ]
        detail = f"; conflicting stored knowledge: {opposing[0]}" if opposing else ""
        return make_conclusion(
            strategy="grounded",
            statement=f"CONTESTED: retrieved context conflicts about this ({top.text}{detail})",
            confidence=0.0,
            reasoning=[
                f"grounded on {top.source} {top.reference} at belief {top.belief():.2f}",
                "context contains a detected contradiction; AURA will not pick a side",
            ],
            supports=[item.reference for item in candidates],
        )

    lead = _LEAD.get(top.source, "From retrieved context")
    if len(candidates) == 1:
        statement = f"{lead}: {top.text}"
    else:
        statement = (
            f"{lead} ({len(candidates)} relevant items, highest ranked): {top.text}"
        )
    return make_conclusion(
        strategy="grounded",
        statement=statement,
        confidence=top.belief(),
        reasoning=[
            f"grounded on {top.source} {top.reference} "
            f"(relevance {top.score:.2f}, confidence {top.confidence:.2f})",
            *[f"also considered {item.source} {item.reference}" for item in candidates[1:]],
        ],
        supports=[item.reference for item in candidates],
    )


def grounding_uncertainty(items: tuple[GroundingItem, ...]) -> UncertaintyLevel:
    """Uncertainty implied by the strongest groundable item."""
    candidates = groundable_items(items)
    if not candidates:
        return UncertaintyLevel.HIGH
    return uncertainty_from_confidence(candidates[0].belief())


__all__ = [
    "MIN_GROUNDING_BELIEF",
    "build_grounded_conclusion",
    "groundable_items",
    "grounding_uncertainty",
]