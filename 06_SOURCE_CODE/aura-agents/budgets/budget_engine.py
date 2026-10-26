"""Budget engine: attach budgets, check limits, and account consumption."""

from __future__ import annotations

from dataclasses import dataclass

from aura_agent.budgets.models.agent_budget import AgentBudget, BudgetLedger
from aura_agent.contracts.errors import BudgetExceeded
from aura_agent.contracts.ids import ExecutionId

__all__ = ["BudgetEngine", "BudgetDecision"]


@dataclass(frozen=True)
class BudgetDecision:
    """Result of a budget check."""

    allowed: bool
    exceeded: list[str]
    reason: str = ""

    @property
    def is_ok(self) -> bool:
        return self.allowed


class BudgetEngine:
    """The single budget authority for executions.

    ``check_execution`` evaluates a projected consumption against the
    attached budget; nothing is consumed by a check. ``consume`` records
    actual consumption and is the only way the ledger mutates.
    """

    def __init__(self) -> None:
        self._ledger = BudgetLedger()
        self._attachments: dict[ExecutionId, AgentBudget] = {}

    def attach(self, execution_id: ExecutionId, budget: AgentBudget) -> None:
        budget.validate()
        self._ledger.open(execution_id)
        self._attachments[execution_id] = budget

    def acquire(self, execution_id: ExecutionId) -> AgentBudget | None:
        return self._attachments.get(execution_id)

    def check_execution(
        self,
        execution_id: ExecutionId,
        projection: dict[str, float] | None = None,
    ) -> BudgetDecision:
        """Check a projected/additional consumption against the budget.

        ``projection`` is the *additional* amount the caller intends to
        consume. The check is read-only: it never mutates the ledger.
        """
        budget = self._attachments.get(execution_id)
        if budget is None:
            return BudgetDecision(allowed=False, exceeded=["__no_budget__"], reason="no budget attached")

        current = self._ledger.snapshot(execution_id).consumed
        projection = projection or {}
        exceeded: list[str] = []
        for dim, amount in projection.items():
            if amount < 0:
                return BudgetDecision(allowed=False, exceeded=[dim], reason=f"negative projection for {dim}")
            projected_total = current.get(dim, 0.0) + amount
            if projected_total > budget.limit(dim):
                exceeded.append(dim)
        if exceeded:
            return BudgetDecision(
                allowed=False,
                exceeded=exceeded,
                reason=f"budget would be exceeded in {sorted(exceeded)!r}",
            )
        return BudgetDecision(allowed=True, exceeded=[], reason="budget ok")

    def consume(self, execution_id: ExecutionId, *, dimension: str, amount: float) -> None:
        """Record actual consumption, refusing over-limit usage."""
        if amount < 0:
            raise ValueError("budget consumption may not be negative")
        budget = self._attachments.get(execution_id)
        limit = budget.limit(dimension) if budget else float("inf")
        current = self._ledger.snapshot(execution_id).consumed.get(dimension, 0.0)
        if current + amount > limit + 1e-9:
            raise BudgetExceeded(
                f"budget dimension {dimension!r} exceeded: {current + amount:g} > {limit:g}"
            )
        self._ledger.consume(execution_id, dimension, amount)

    def snapshot(self, execution_id: ExecutionId) -> dict[str, float]:
        return self._ledger.snapshot(execution_id).consumed

    def remaining(self, execution_id: ExecutionId) -> dict[str, float]:
        budget = self._attachments.get(execution_id)
        consumed = self._ledger.snapshot(execution_id).consumed
        if budget is None:
            return {}
        return {
            dim: max(0.0, budget.limit(dim) - consumed.get(dim, 0.0))
            for dim in budget.limits
        }
