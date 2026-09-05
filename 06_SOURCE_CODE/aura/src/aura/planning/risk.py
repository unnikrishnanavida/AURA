"""Plan risk analysis.

Before execution evaluate risk, estimated cost, required capabilities and
permissions, dependency depth, and rollback feasibility.
"""

from __future__ import annotations

from aura.planning.models import PlanRisk, Task


class RiskAnalyzer:
    def analyze(self, tasks: list[Task]) -> PlanRisk:
        if not tasks:
            return PlanRisk(
                level="low", score=0.0, cost_estimate=0.0, time_estimate=0.0,
                required_capabilities=(), required_permissions=(), rollback_feasible=True,
            )

        cost = sum(t.estimated_cost for t in tasks)
        time_estimate = sum(t.estimated_seconds for t in tasks)
        capabilities = tuple(sorted({t.capability for t in tasks}))
        max_task_risk = max(t.risk for t in tasks)
        avg_task_risk = sum(t.risk for t in tasks) / len(tasks)
        depth = max((len(t.prerequisites) for t in tasks), default=0)

        score = min(1.0, max_task_risk * 0.6 + avg_task_risk * 0.3 + (depth / 10.0) * 0.1)
        rollback_feasible = all(t.rollback_feasible for t in tasks)
        concerns: list[str] = []
        if max_task_risk >= 0.7:
            concerns.append(f"high-risk task present (risk {max_task_risk:.2f})")
        if not rollback_feasible:
            concerns.append("some tasks are not rollback feasible")
        if depth >= 5:
            concerns.append(f"deep dependency chain (depth {depth})")

        level = "low"
        if score >= 0.7:
            level = "high"
        elif score >= 0.4:
            level = "medium"

        permissions = tuple(capabilities)
        return PlanRisk(
            level=level,
            score=round(score, 6),
            cost_estimate=round(cost, 4),
            time_estimate=round(time_estimate, 4),
            required_capabilities=capabilities,
            required_permissions=permissions,
            rollback_feasible=rollback_feasible,
            concerns=tuple(concerns),
        )


__all__ = ["RiskAnalyzer"]