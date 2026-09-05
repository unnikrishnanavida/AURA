"""Cost budget for aura-cloud deployments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostBudget:
    """A per-deployment or per-period cost ceiling."""

    max_cost: float
    spent: float = 0.0

    def charge(self, amount: float) -> bool:
        """Charge against the budget; returns False when the ceiling would be
        exceeded (the charge is NOT applied)."""
        if amount < 0:
            raise ValueError("negative cost not allowed")
        if self.spent + amount > self.max_cost:
            return False
        self.spent += amount
        return True

    def allows(self, amount: float) -> bool:
        return self.spent + amount <= self.max_cost

    @property
    def remaining(self) -> float:
        return max(0.0, self.max_cost - self.spent)


@dataclass
class CostEstimate:
    """A truthful cost estimate for a deployment plan."""

    provider: str
    estimated: float
    currency: str = "USD"

    def to_dict(self) -> dict[str, object]:
        return {"provider": self.provider, "estimated": self.estimated, "currency": self.currency}


__all__ = ["CostBudget", "CostEstimate"]