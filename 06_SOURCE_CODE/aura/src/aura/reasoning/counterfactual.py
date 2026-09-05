"""Counterfactual strategy.

What-if reasoning: flip one variable and recompute consequences through the
causal rules. The result states the hypothetical outcome explicitly.
"""

from __future__ import annotations

from aura.reasoning.models import InferenceStep, ReasoningInput, make_conclusion


class CounterfactualStrategy:
    name = "counterfactual"

    def reason(self, inp: ReasoningInput) -> object:
        variable = inp.counterfactual_variable
        if not variable:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: counterfactual variable not specified for {inp.question!r}",
                confidence=0.0,
                reasoning=["counterfactual reasoning requires a variable to perturb"],
            )

        original = inp.facts.get(variable, 0.0)
        flipped = 1.0 - (1.0 if original >= 0.5 else 0.0)
        beliefs: dict[str, float] = dict(inp.facts)
        beliefs[variable] = flipped
        steps: list[InferenceStep] = []

        fired = True
        guard = 0
        while fired and guard < len(inp.rules) + 1:
            fired = False
            guard += 1
            for rule in inp.rules:
                if rule.consequent in beliefs:
                    continue
                if not all(beliefs.get(c, 0.0) >= 0.5 for c in rule.conditions):
                    continue
                beliefs[rule.consequent] = min(beliefs[c] for c in rule.conditions) * rule.weight
                steps.append(
                    InferenceStep(rule.id, rule.conditions, rule.consequent, beliefs[rule.consequent])
                )
                fired = True

        if inp.question not in beliefs:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: flipping {variable!r} does not affect {inp.question!r}",
                confidence=0.0,
                reasoning=["perturbation produced no path to the question"],
            )

        return make_conclusion(
            strategy=self.name,
            statement=f"if {variable} had been true, then {inp.question} would hold",
            confidence=beliefs[inp.question],
            reasoning=[f"perturbation: {variable} -> {flipped:.0f}", *(s.derived for s in steps)],
            supports=[s.rule_id for s in steps],
        )


__all__ = ["CounterfactualStrategy"]