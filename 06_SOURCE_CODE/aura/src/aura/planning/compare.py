"""Plan comparison.

Ranks alternative plans by a weighted score over estimated cost, safety, and
execution time. Lower score wins.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.planning.models import Plan


@dataclass(frozen=True)
class PlanComparison:
    plan: Plan
    score: float

    def to_dict(self) -> dict[str, object]:
        return {"plan_id": str(self.plan.id), "score": self.score}


class PlanComparator:
    def __init__(self, *, cost_weight: float = 0.4, risk_weight: float = 0.4, time_weight: float = 0.2) -> None:
        self.cost_weight = cost_weight
        self.risk_weight = risk_weight
        self.time_weight = time_weight

    def compare(self, plans: list[Plan]) -> list[PlanComparison]:
        scored: list[PlanComparison] = []
        for plan in plans:
            cost_n = min(1.0, plan.risk.cost_estimate / 100.0)
            time_n = min(1.0, plan.risk.time_estimate / 120.0)
            score = (
                self.cost_weight * cost_n
                + self.risk_weight * plan.risk.score
                + self.time_weight * time_n
            )
            scored.append(PlanComparison(plan=plan, score=round(score, 6)))
        scored.sort(key=lambda c: c.score)
        return scored

    def best(self, plans: list[Plan]) -> Plan | None:
        comparisons = self.compare(plans)
        return comparisons[0].plan if comparisons else None


__all__ = ["PlanComparator", "PlanComparison"]