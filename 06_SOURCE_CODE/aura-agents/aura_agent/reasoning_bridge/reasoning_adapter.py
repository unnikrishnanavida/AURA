"""Reasoning provider protocol and the reasoning adapter.

The adapter is provider-independent. The built-in ``RuleBasedReasoner`` is a
deterministic, offline implementation for testing and default operation; other
AURA Reasoning providers can be plugged in behind the same protocol. The
bridge never hardcodes an LLM provider.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aura_agent.reasoning_bridge.models import ReasoningRequest, ReasoningResult

__all__ = ["ReasoningProvider", "RuleBasedReasoner", "ReasoningBridge"]


@runtime_checkable
class ReasoningProvider(Protocol):
    def reason(self, request: ReasoningRequest) -> ReasoningResult: ...


class RuleBasedReasoner:
    """Deterministic rule-based reasoning used when no external provider is
    configured. Understands a tiny, well-defined intent vocabulary."""

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        objective = (request.objective or "").lower()
        context = request.context or {}

        if "risk" in objective or "approval" in objective:
            risk = float(context.get("risk_score", 0.0))
            answer = "proceed" if risk < 0.5 else "request_approval"
        elif "capability" in objective or "can_we" in objective:
            answer = "yes" if context.get("capability_matched") else "no"
        elif "which_tool" in objective or "tool" in objective:
            candidates = context.get("candidate_tools") or []
            answer = candidates[0] if candidates else "none_available"
        else:
            answer = "no_usable_plan"
        return ReasoningResult(
            answer=answer,
            confidence=0.8,
            metadata={"provider": "rule_based", "objective": objective},
            provider="rule_based",
        )


class ReasoningBridge:
    """Fans reasoning requests out to a provider and adapts the result."""

    def __init__(self, provider: ReasoningProvider | None = None) -> None:
        self._provider = provider or RuleBasedReasoner()

    @property
    def provider(self) -> ReasoningProvider:
        return self._provider

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        result = self._provider.reason(request)
        # normalize confidence into [0, 1]
        confidence = max(0.0, min(1.0, float(result.confidence)))
        return ReasoningResult(
            answer=result.answer,
            confidence=confidence,
            metadata=result.metadata,
            provider=result.provider,
        )
