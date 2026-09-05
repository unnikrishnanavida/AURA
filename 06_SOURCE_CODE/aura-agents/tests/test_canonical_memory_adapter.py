"""Canonical AURA memory adapter tests.

These tests prove the agent runtime can delegate memory reads/writes to the
canonical ``aura.memory.MemoryEngine`` through the ``MemoryProvider`` protocol,
with no duplicated engine logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aura_agent.memory_bridge.canonical_adapter import CanonicalMemoryProvider  # noqa: E402
from aura_agent.memory_bridge.models import MemoryEntry, MemoryQuery  # noqa: E402


@pytest.fixture
def canonical_engine() -> object:
    from aura.foundation.clock import ManualClock
    from aura.memory.engine import MemoryEngine

    return MemoryEngine(clock=ManualClock(0))


@pytest.fixture
def provider(canonical_engine: object) -> CanonicalMemoryProvider:
    return CanonicalMemoryProvider(canonical_engine)


def test_write_through_canonical_memory(provider: CanonicalMemoryProvider, canonical_engine: object) -> None:
    provider.write(MemoryEntry(key="deploy:canary", kind="experience", content={"ok": True}))
    assert canonical_engine.store.count() == 1  # type: ignore[attr-defined]


def test_retrieve_round_trip(provider: CanonicalMemoryProvider, canonical_engine: object) -> None:
    provider.write(MemoryEntry(key="deploy:canary", kind="experience", content={"ok": True}))
    records = provider.retrieve(MemoryQuery(key="deploy:canary", limit=5))
    assert len(records) == 1
    assert records[0].entry.key == "deploy:canary"
    assert records[0].score >= 0.0


def test_kind_filter(provider: CanonicalMemoryProvider, canonical_engine: object) -> None:
    provider.write(MemoryEntry(key="fact:hosts", kind="semantic", content={"n": 3}))
    provider.write(MemoryEntry(key="exp:run-1", kind="outcome", content={"succeeded": False}))
    semantic = provider.retrieve(MemoryQuery(kind="semantic", limit=10))
    episodic = provider.retrieve(MemoryQuery(kind="episodic", limit=10))
    assert len(semantic) == 1
    assert len(episodic) == 1


def test_agent_bridge_delegates_to_canonical(provider: CanonicalMemoryProvider) -> None:
    from aura_agent.memory_bridge.memory_adapter import MemoryBridge

    bridge = MemoryBridge(provider=provider)
    bridge.write_experience(
        __import__("aura_agent.memory_bridge.models", fromlist=["Experience"]).Experience(
            action="run-analysis", succeeded=True
        )
    )
    hits = bridge.retrieve(MemoryQuery(key="exp:run-analysis"))
    assert hits and hits[0].entry.content["succeeded"] is True