"""Abductive strategy: best explanation.

Given observed facts and rules, candidate explanations are the premise sets of
rules whose consequents are observed. Rank by coverage, simplicity, and rule
weight.
"""

from __future__ import annotations

from aura.reasoning.models import ReasoningInput, Rule, make_conclusion


class AbductiveStrategy:
    name = "abductive"

    def reason(self, inp: ReasoningInput) -> object:
        observed = inp.observed_propositions
        candidates: list[Rule] = [
            rule
            for rule in inp.rules
            if rule.consequent in observed or rule.consequent == inp.question
        ]
        if not candidates and inp.hypotheses:
            candidates = [Rule(id=hyp, conditions=tuple(observed), consequent=hyp) for hyp in inp.hypotheses]

        if not candidates:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: no explanation candidate for {inp.question!r}",
                confidence=0.0,
                reasoning=["no rule connects observations to the question"],
            )

        scored: list[tuple[float, Rule]] = []
        for rule in candidates:
            conditions = list(rule.conditions)
            hits = sum(1 for c in conditions if c in observed)
            coverage = hits / len(conditions) if conditions else 0.0
            simplicity = 1.0 / (1.0 + len(conditions))
            scored.append((rule.weight * coverage * simplicity, rule))
        scored.sort(key=lambda item: item[0], reverse=True)

        best_score, best = scored[0]
        reasoning = [
            f"{rule.consequent} explained by {', '.join(rule.conditions)} (score {score:.3f})"
            for score, rule in scored[:5]
        ]
        alternatives = [
            rule.consequent
            for score, rule in scored[1:4]
            if score > 0.0 and rule.consequent != best.consequent
        ]
        return make_conclusion(
            strategy=self.name,
            statement=f"{best.consequent} best explains {sorted(observed)}",
            confidence=min(1.0, best_score * 2.0),
            reasoning=reasoning,
            supports=[best.id],
            alternatives=alternatives,
        )


__all__ = ["AbductiveStrategy"]