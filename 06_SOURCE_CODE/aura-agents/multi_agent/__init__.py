"""Multi-agent: communication, message bus, and coordination."""

from aura_agent.multi_agent.communication.message_bus import MessageBus
from aura_agent.multi_agent.communication.models import AgentMessage, MessageEnvelope
from aura_agent.multi_agent.coordination.coordinator import (
    CoordinationRole,
    CoordinationState,
    Coordinator,
    SharedGoal,
)

__all__ = [
    "MessageBus",
    "AgentMessage",
    "MessageEnvelope",
    "Coordinator",
    "CoordinationRole",
    "CoordinationState",
    "SharedGoal",
]
