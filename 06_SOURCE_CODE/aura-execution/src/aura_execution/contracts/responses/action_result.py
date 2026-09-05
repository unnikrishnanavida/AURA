"""Action-level result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionResult:
    """The result of dispatching a single action handler."""

    success: bool
    value: Any = None
    error: str | None = None
    duration: float = 0.0
    details: dict[str, Any] | None = None


__all__ = ["ActionResult"]