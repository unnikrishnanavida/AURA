"""Message bus: in-memory asynchronous delivery between agents.

The bus keeps an inbox per agent and delivers messages deterministically in
arrival order. It is intentionally in-memory and dependency-free; a durable
bus can replace it behind the same API.
"""

from __future__ import annotations

from collections import defaultdict

from aura_agent.contracts.ids import AgentId
from aura_agent.multi_agent.communication.models import AgentMessage, MessageEnvelope

__all__ = ["MessageBus"]


class MessageBus:
    """Synchronous in-process message dispatch with per-agent inboxes."""

    def __init__(self) -> None:
        self._inboxes: dict[AgentId, list[MessageEnvelope]] = defaultdict(list)
        self._sent_log: list[AgentMessage] = []

    def send(self, message: AgentMessage) -> None:
        self._inboxes[message.recipient].append(MessageEnvelope(message=message))
        self._sent_log.append(message)

    def receive(self, agent_id: AgentId) -> list[AgentMessage]:
        """Drain the inbox for ``agent_id`` and return its messages."""
        envelopes = self._inboxes.pop(agent_id, [])
        return [e.message for e in envelopes]

    def peek(self, agent_id: AgentId) -> list[AgentMessage]:
        return [e.message for e in self._inboxes.get(agent_id, [])]

    def sent(self) -> list[AgentMessage]:
        return list(self._sent_log)

    def clear(self) -> None:
        self._inboxes.clear()
        self._sent_log.clear()