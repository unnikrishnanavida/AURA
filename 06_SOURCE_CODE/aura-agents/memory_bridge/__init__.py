"""Memory bridge: Agent <-> AURA Memory integration via injected providers."""

from aura_agent.memory_bridge.memory_adapter import (
    InMemoryMemory,
    MemoryBridge,
    MemoryProvider,
)
from aura_agent.memory_bridge.models import (
    Experience,
    MemoryEntry,
    MemoryQuery,
    MemoryRecord,
)

__all__ = [
    "MemoryProvider",
    "InMemoryMemory",
    "MemoryBridge",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryRecord",
    "Experience",
]
