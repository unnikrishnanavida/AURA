"""Deductive strategy: forward chaining over rules.

Deterministic, monotonic inference from observed facts through rules until the
question is derived or no rule can fire.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aura.reasoning.models import InferenceStep, ReasoningInput, make_conclusion


@runtime_checkable
class Strategy(Protocol):
    name: str

    def reason(self, inp: ReasoningInput) -> object: ...


class DeductiveStrategy:
    name = "deductive"

    def reason(self, inp: ReasoningInput) -> object:
        beliefs: dict[str, float] = dict(inp.facts)
        steps: list[InferenceStep] = []
        fired = True
        guard = 0
        while fired and guard < len(inp.rules) + 1:
            fired = False
            guard += 1
            for rule in inp.rules:
                if rule.consequent in beliefs:
                    continue
                if not all(rule.conditions[idx] in beliefs for idx in range(len(rule.conditions))):
                    continue
                premise_conf = min(beliefs[c] for c in rule.conditions)
                derived_conf = premise_conf * rule.weight
                beliefs[rule.consequent] = derived_conf
                steps.append(
                    InferenceStep(rule.id, rule.conditions, rule.consequent, round(derived_conf, 6))
                )
                fired = True

        reasoning_lines = [
            f"{step.derived} at {step.confidence:.2f} via {step.rule_id}" for step in steps
        ]
        if inp.question not in beliefs:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: insufficient premises to derive {inp.question!r}",
                confidence=0.0,
                reasoning=reasoning_lines or ["no rule fired for the question"],
                alternatives=sorted({b for b, c in beliefs.items() if c >= 0.5 and b != inp.question}),
            )
        return make_conclusion(
            strategy=self.name,
            statement=inp.question,
            confidence=beliefs[inp.question],
            reasoning=reasoning_lines,
            supports=[s.rule_id for s in steps],
        )


__all__ = ["DeductiveStrategy", "Strategy"]