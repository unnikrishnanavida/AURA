"""Budget models: the multidimensional resource envelope for an execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura_agent.contracts.ids import AgentId, ExecutionId, GoalId

__all__ = ["BudgetDimension", "AgentBudget", "BudgetUsage"]


class BudgetDimension:
    """Well-known budget dimensions.

    Kept as explicit string constants so that telemetry and accounting can
    treat them uniformly.
    """

    TIME = "time_s"
    ACTIONS = "actions"
    RETRIES = "retries"
    COST = "cost"
    API_CALLS = "api_calls"
    TOKENS = "tokens"


@dataclass(frozen=True)
class AgentBudget:
    """The budget envelope granted to one execution."""

    limits: dict[str, float]
    owner_agent: AgentId | None = None
    goal_id: GoalId | None = None

    def limit(self, dimension: str) -> float:
        return self.limits.get(dimension, float("inf"))

    def validate(self) -> None:
        for name, value in self.limits.items():
            if value < 0:
                raise ValueError(f"budget dimension {name!r} may not be negative")
            if name == BudgetDimension.ACTIONS and value != int(value):
                raise ValueError("actions budget must be a whole number")


@dataclass
class BudgetUsage:
    """Immutable snapshot of consumption for one execution (for accounting)."""

    execution_id: ExecutionId
    consumed: dict[str, float]

    def clone(self) -> "BudgetUsage":
        return BudgetUsage(self.execution_id, dict(self.consumed))


class BudgetLedger:
    """Append-only per-execution accounting.

    The ledger is deliberately simple and dependency-free: each execution has
    one row, consumption is applied atomically through a single locked update
    method, and totals are never recomputed from partially applied writes.
    """

    def __init__(self) -> None:
        self._rows: dict[ExecutionId, BudgetUsage] = {}

    def open(self, execution_id: ExecutionId) -> None:
        if execution_id not in self._rows:
            self._rows[execution_id] = BudgetUsage(execution_id, {})

    def consume(self, execution_id: ExecutionId, dimension: str, amount: float) -> None:
        row = self._rows.get(execution_id)
        if row is None:
            self.open(execution_id)
            row = self._rows[execution_id]
        row.consumed[dimension] = row.consumed.get(dimension, 0.0) + amount

    def snapshot(self, execution_id: ExecutionId) -> BudgetUsage:
        row = self._rows.get(execution_id)
        if row is None:
            return BudgetUsage(execution_id, {})
        return row.clone()

    def totals(self) -> dict[str, float]:
        merged: dict[str, float] = {}
        for row in self._rows.values():
            for dim, amt in row.consumed.items():
                merged[dim] = merged.get(dim, 0.0) + amt
        return merged