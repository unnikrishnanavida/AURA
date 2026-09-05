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
    "Assumption",
    "Case",
    "Conclusion",
    "InferenceStep",
    "ReasoningInput",
    "ReasoningTrace",
    "Rule",
    "make_conclusion",
]