"""Multi-agent communication, coordination, and message models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.ids import AgentId

__all__ = ["AgentMessage", "MessageEnvelope"]


@dataclass(frozen=True)
class AgentMessage:
    """A single message between agents.

    ``reply_to`` correlates replies to original messages; ``payload`` is a
    JSON-serializable body.
    """

    kind: str  # "request" | "response" | "proposal" | "ack" | "broadcast"
    sender: AgentId
    recipient: AgentId
    payload: dict = field(default_factory=dict)
    message_id: str = ""
    reply_to: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class MessageEnvelope:
    """A dispatched message with delivery metadata."""

    message: AgentMessage
    delivered_at: datetime = field(default_factory=lambda: datetime.now(UTC))