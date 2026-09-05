"""Budgets.

Multi-dimensional budget accounting (actions, seconds, cost, tokens). Budget
checks are nested inside the guardrail pipeline; no stage may bypass an
exhausted budget.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from aura.config.settings import BudgetLimits
from aura.foundation.errors import BudgetExhaustedError, ValidationError


@dataclass(frozen=True)
class BudgetStatus:
    actions: int
    actions_limit: int
    seconds: float
    seconds_limit: float
    cost: float
    cost_limit: float
    tokens: int
    tokens_limit: int

    @property
    def exhausted(self) -> bool:
        return (
            self.actions >= self.actions_limit
            or self.seconds >= self.seconds_limit
            or self.cost >= self.cost_limit
            or self.tokens >= self.tokens_limit
        )


class BudgetTracker:
    def __init__(self, limits: BudgetLimits | None = None) -> None:
        self._limits = limits or BudgetLimits()
        self._actions = 0
        self._cost = 0.0
        self._tokens = 0
        self._started = time.monotonic()
        self._lock = threading.RLock()

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self._started

    def status(self) -> BudgetStatus:
        with self._lock:
            return BudgetStatus(
                actions=self._actions,
                actions_limit=self._limits.max_actions,
                seconds=self.elapsed_seconds,
                seconds_limit=self._limits.max_seconds,
                cost=self._cost,
                cost_limit=self._limits.max_cost,
                tokens=self._tokens,
                tokens_limit=self._limits.max_tokens,
            )

    def check(self) -> BudgetStatus:
        status = self.status()
        if status.exhausted:
            raise BudgetExhaustedError(
                f"budget exhausted: {status.actions}/{status.actions_limit} actions, "
                f"{status.seconds:.1f}/{status.seconds_limit}s, "
                f"{status.cost:.2f}/{status.cost_limit} cost, "
                f"{status.tokens}/{status.tokens_limit} tokens"
            )
        return status

    def consume(self, *, actions: int = 0, cost: float = 0.0, tokens: int = 0) -> None:
        if actions < 0 or cost < 0 or tokens < 0:
            raise ValidationError("budget consumption must be non-negative")
        with self._lock:
            self._actions += actions
            self._cost += cost
            self._tokens += tokens
        self.check()

    def reset(self) -> None:
        with self._lock:
            self._actions = 0
            self._cost = 0.0
            self._tokens = 0
            self._started = time.monotonic()


__all__ = ["BudgetStatus", "BudgetTracker"]