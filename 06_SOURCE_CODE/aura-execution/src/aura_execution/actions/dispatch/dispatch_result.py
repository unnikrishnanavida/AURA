"""Dispatch result used by the action dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DispatchResult:
    """Outcome of invoking an action handler."""

    success: bool
    value: Any = None
    error: str | None = None
    duration: float = 0.0


__all__ = ["DispatchResult"]