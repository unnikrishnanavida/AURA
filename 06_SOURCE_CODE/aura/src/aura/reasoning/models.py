"""Reasoning domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.reasoning.uncertainty import UncertaintyLevel, uncertainty_from_confidence


@dataclass(frozen=True, slots=True)
class Rule:
    """An if-conditions-then-consequent rule with a confidence weight."""

    id: str
    conditions: tuple[str, ...]
    consequent: str
    weight: float = 0.8

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"rule weight must be in [0,1], got {self.weight}")


@dataclass(frozen=True, slots=True)
class Case:
    """A base case for analogical reasoning."""

    attrs: frozenset[str]
    outcome: str
    strength: float = 1.0


@dataclass(frozen=True, slots=True)
class Assumption:
    statement: str
    confidence: float = 0.7
    defeasible: bool = True


@dataclass(frozen=True, slots=True)
class InferenceStep:
    rule_id: str
    from_propositions: tuple[str, ...]
    derived: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ReasoningTrace:
    steps: list[InferenceStep] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)

    def lines(self) -> list[str]:
        return [
            f"{step.derived} (from {', '.join(step.from_propositions)} via {step.rule_id} "
            f"at {step.confidence:.2f})"
            for step in self.steps
        ]


@dataclass(frozen=True, slots=True)
class Conclusion:
    strategy: str
    statement: str
    confidence: float
    uncertainty: UncertaintyLevel
    reasoning: tuple[str, ...] = ()
    supports: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "statement": self.statement,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty.value,
            "reasoning": list(self.reasoning),
            "supports": list(self.supports),
            "alternatives": list(self.alternatives),
        }


@dataclass(frozen=True, slots=True)
class GroundingItem:
    """One retrieved, attributable piece of context for a single question.

    A grounding item is *evidence*, not assertion: it carries the record it came
    from, how relevant it scored, how confident the source is, and whether the
    knowledge base currently contradicts it. Nothing here is ever invented --
    every field is derived from a stored memory entry or knowledge claim.
    """

    source: str  # "memory" | "knowledge"
    reference: str  # memory id or claim id
    text: str
    score: float  # relevance in [0,1]
    confidence: float  # source confidence in [0,1]
    verified: bool = False
    contradicted: bool = False
    scope: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def belief(self) -> float:
        """Deterministic belief this item contributes to the fact base.

        Confidence and relevance are multiplied (neither alone justifies a
        fact), and contradicted evidence is discounted rather than dropped so
        the conflict remains visible to verification.
        """
        base = self.confidence * self.score
        if self.contradicted:
            base *= 0.4
        return round(min(1.0, max(0.0, base)), 6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "reference": self.reference,
            "text": self.text,
            "score": round(self.score, 6),
            "confidence": round(self.confidence, 6),
            "belief": self.belief(),
            "verified": self.verified,
            "contradicted": self.contradicted,
            "scope": self.scope,
            "provenance": dict(self.provenance),
        }


#: Matches :meth:`ReasoningInput.observed`: a proposition counts as observed at
#: or above this belief. Retrieved context below it is still returned for
#: attribution and may still ground an extractive answer, but it is never
#: promoted into a logical premise -- a sentence someone once stored is not a
#: premise the reasoner may derive from.
OBSERVED_BELIEF = 0.5


@dataclass(frozen=True, slots=True)
class Grounding:
    """The explicit context contract handed to one reasoning pass.

    ``items`` is relevance-ranked and budget-bounded by the assembler;
    ``dropped``/``truncated`` record what the budget removed so a caller can
    always tell the difference between "nothing was relevant" and "the context
    budget cut the relevant items off".
    """

    items: tuple[GroundingItem, ...] = ()
    contradictions: tuple[tuple[str, str], ...] = ()
    dropped: int = 0
    truncated: bool = False
    filtered: int = 0
    turns: int = 0

    def facts(self) -> dict[str, float]:
        """Facts contributed by the context; caller-supplied facts take priority.

        Only items at or above :data:`OBSERVED_BELIEF` qualify, so weakly
        supported context cannot distort the deterministic strategies.
        """
        return {
            item.text: item.belief()
            for item in self.items
            if item.text and item.belief() >= OBSERVED_BELIEF
        }

    def evidence_lines(self) -> tuple[str, ...]:
        return tuple(f"[{item.source}] {item.text}" for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "contradictions": [list(pair) for pair in self.contradictions],
            "dropped": self.dropped,
            "truncated": self.truncated,
            "filtered": self.filtered,
            "turns": self.turns,
        }


@dataclass
class ReasoningInput:
    """Everything a strategy may need to answer one question."""

    question: str
    facts: dict[str, float]
    rules: tuple[Rule, ...] = ()
    hypotheses: tuple[str, ...] = ()
    likelihoods: dict[str, tuple[float, float]] = field(default_factory=dict)
    prior: float = 0.5
    cases: tuple[Case, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    min_evidence: int = 1
    counterfactual_variable: str = ""
    grounding: Grounding = field(default_factory=Grounding)

    def observed(self, proposition: str) -> bool:
        return self.facts.get(proposition, 0.0) >= 0.5

    @property
    def observed_propositions(self) -> set[str]:
        return {p for p, v in self.facts.items() if v >= 0.5}


def make_conclusion(
    *,
    strategy: str,
    statement: str,
    confidence: float,
    reasoning: list[str],
    supports: list[str] | tuple[str, ...] = (),
    alternatives: list[str] | tuple[str, ...] = (),
) -> Conclusion:
    return Conclusion(
        strategy=strategy,
        statement=statement,
        confidence=round(min(1.0, max(0.0, confidence)), 6),
        uncertainty=uncertainty_from_confidence(confidence),
        reasoning=tuple(reasoning),
        supports=tuple(supports),
        alternatives=tuple(alternatives),
    )


__all__ = [
    "OBSERVED_BELIEF",
    "Assumption",
    "Case",
    "Conclusion",
    "Grounding",
    "GroundingItem",
    "InferenceStep",
    "ReasoningInput",
    "ReasoningTrace",
    "Rule",
    "make_conclusion",
]