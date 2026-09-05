"""AURA cognitive memory.

Authoritative memory system with working/episodic/semantic/procedural
separation, confidence, provenance, linking, consolidation, forgetting, and
replay support. Persistence lives behind the :class:`MemoryStore` contract:
in-memory (development), SQLite (file-backed), and a PostgreSQL-ready protocol.
"""

from __future__ import annotations

from aura.memory.consolidation import Consolidator, ForgettingPolicy
from aura.memory.engine import MemoryEngine, MemoryQuery
from aura.memory.factory import create_memory_store
from aura.memory.graph import MemoryGraph
from aura.memory.models import (
    LinkKind,
    MemoryConfidence,
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from aura.memory.policy import MemoryLifecycle, MemoryPolicy
from aura.memory.retrieval import RetrievalScorer
from aura.memory.serialization import entry_to_row, row_to_entry
from aura.memory.sqlite_store import SQLiteMemoryStore
from aura.memory.store import InMemoryMemoryStore, MemoryStore

__all__ = [
    "Consolidator",
    "ForgettingPolicy",
    "InMemoryMemoryStore",
    "LinkKind",
    "MemoryConfidence",
    "MemoryEngine",
    "MemoryEntry",
    "MemoryGraph",
    "MemoryLifecycle",
    "MemoryPolicy",
    "MemoryQuery",
    "MemoryStatus",
    "MemoryStore",
    "MemoryType",
    "Provenance",
    "RetentionPolicy",
    "RetrievalScorer",
    "Sensitivity",
    "SQLiteMemoryStore",
    "create_memory_store",
    "entry_to_row",
    "row_to_entry",
]