"""Probabilistic strategy: Bayesian updating.

Uses explicit priors and likelihood ratios. With no observations it reports
the prior honestly as HIGH uncertainty — it does not invent evidence.
"""

from __future__ import annotations

from aura.reasoning.models import ReasoningInput, make_conclusion


class BayesianStrategy:
    name = "probabilistic"

    def reason(self, inp: ReasoningInput) -> object:
        posterior = max(0.0, min(1.0, inp.prior))
        applied: list[str] = []
        for evidence, (if_yes, if_no) in inp.likelihoods.items():
            if inp.observed(evidence) and 0.0 <= if_yes <= 1.0 and 0.0 <= if_no <= 1.0:
                likelihood_ratio = if_yes / if_no if if_no > 0 else (1e6 if if_yes > 0 else 1.0)
                odds = (posterior / (1.0 - posterior)) * likelihood_ratio if posterior < 1.0 else 1e6
                posterior = min(1.0, odds / (1.0 + odds))
                applied.append(f"updated on {evidence}")

        if not applied:
            return make_conclusion(
                strategy=self.name,
                statement=f"{inp.question} (prior {posterior:.2f}, no observations)",
                confidence=posterior,
                reasoning=["no observations supplied; posterior equals prior"],
            )
        return make_conclusion(
            strategy=self.name,
            statement=inp.question,
            confidence=posterior,
            reasoning=applied,
            supports=[af.split("on ")[1] for af in applied],
        )


__all__ = ["BayesianStrategy"]