"""End-to-end SDK tests: the public AURA surface."""

from __future__ import annotations

from aura.foundation.clock import ManualClock
from aura.memory.models import MemoryType
from aura.planning.models import Goal, Task
from aura.sdk.client import Aura


def make_aura() -> Aura:
    return Aura(clock=ManualClock(0), seed=11)


def test_sdk_reason_returns_structure() -> None:
    aura = make_aura()
    result = aura.reason("test")
    assert set(result) >= {"execution_id", "answer", "confidence", "uncertainty", "steps"}


def test_sdk_from_root_import() -> None:
    import aura as root

    instance = root.Aura(clock=ManualClock(0), seed=1)
    assert instance.health()["status"] == "ok"


def test_sdk_memory_roundtrip() -> None:
    aura = make_aura()
    memory_id = aura.remember("key", {"v": 1}, kind=MemoryType.SEMANTIC)
    assert memory_id.startswith("mem-")
    entries = aura.recall("key")
    assert entries and entries[0]["key"] == "key"


def test_sdk_plan() -> None:
    aura = make_aura()
    plan = aura.plan(
        goal=Goal.create(description="build"),
        tasks=[Task(name="a"), Task(name="b", prerequisites=("a",))],
    )
    assert plan["plan_created"]
    assert plan["steps"] == ["1:a", "2:b"]


def test_sdk_observe_and_health() -> None:
    aura = make_aura()
    claim_id = aura.observe(statement="all systems nominal", predicate=("systems", "status"))
    assert claim_id.startswith("cl-")
    assert aura.health()["status"] == "ok"


def test_sdk_replay_and_provenance() -> None:
    aura = make_aura()
    result = aura.reason("record me", facts={"evidence": 0.7})
    execution_id = result["execution_id"]
    replay = aura.replay(execution_id)
    assert replay["events"]
    provenance = aura.provenance(execution_id)
    assert "cause_chain" in provenance


def test_sdk_reflect() -> None:
    aura = make_aura()
    reflection = aura.reflect(goal="goal", success=True)
    assert "reflections" in reflection


def test_sdk_metrics() -> None:
    aura = make_aura()
    aura.reason("count me")
    snapshot = aura.metrics()
    assert "counters" in snapshot


def test_sdk_provider_profile() -> None:
    aura = make_aura()
    profile = aura.provider_profile
    assert profile.local is True
    assert "reasoning" in profile.kind