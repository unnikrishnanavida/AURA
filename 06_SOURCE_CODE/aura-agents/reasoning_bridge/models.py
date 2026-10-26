"""Reasoning bridge models: provider-independent reasoning contracts.

The reasoning bridge is the Agent <-> AURA Reasoning integration boundary.
Providers implement :class:`~aura_agent.reasoning_bridge.reasoning_adapter.ReasoningProvider`;
the rest of the runtime only ever sees request/result models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["ReasoningRequest", "ReasoningResult"]


@dataclass(frozen=True)
class ReasoningRequest:
    """A request to a reasoning provider.

    ``context`` is the assembled situation, ``objective`` what the agent is
    trying to decide, and ``constraints`` bound the reasoning.
    """

    objective: str
    context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    provider: str = "default"


@dataclass(frozen=True)
class ReasoningResult:
    """A provider answer with confidence and structured metadata."""

    answer: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    provider: str = "default"
