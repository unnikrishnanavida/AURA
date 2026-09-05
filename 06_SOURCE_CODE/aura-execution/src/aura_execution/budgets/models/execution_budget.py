"""Execution budget definition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutionBudget:
    """Limits for a single execution flow."""

    max_actions: int = 100
    max_retries: int = 3
    max_time: float = 300.0
    max_cost: float = 1000.0


__all__ = ["ExecutionBudget"]