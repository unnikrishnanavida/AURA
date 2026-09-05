"""Runtime execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionContext:
    """Per-execution state and constraints passed to engines."""

    execution_id: str
    principal: str
    state: dict[str, Any] = field(default_factory=dict)
    scopes: set[str] = field(default_factory=lambda: {"*"})
    approved: bool = False
    approved_actions: set[str] = field(default_factory=set)
    dry_run: bool = False
    correlation_id: str | None = None


__all__ = ["ExecutionContext"]