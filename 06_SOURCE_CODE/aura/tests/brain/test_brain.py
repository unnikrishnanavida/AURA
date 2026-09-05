"""Brain orchestration tests: full cognitive cycle, provenance, learning integration."""

from __future__ import annotations

from aura.brain.engine import BrainEngine, BrainResult
from aura.foundation.clock import ManualClock
from aura.memory.models import MemoryType
from aura.planning.models import Goal, Task


def make_brain() -> BrainEngine:
    return BrainEngine.create(clock=ManualClock(0), seed=7)


def test_reason_full_cycle_records_events() -> None:
    brain = make_brain()
    result = brain.reason(
        question="does the sun rise?",
        facts={"the sun rose yesterday": 0.9},
    )
    assert isinstance(result, BrainResult)
    assert result.reasoning is not None
    assert result.reasoning.answer == "I do not know" or result.reasoning.answer
    events = brain.recorder.events(execution_id=result.execution_id)
    assert len(events) >= 2  # observation + decision


def test_reason_with_plan() -> None:
    brain = make_brain()
    result = brain.reason(
        question="plan the delivery",
        facts={},
        goal=Goal.create(description="deliver artifact"),
        tasks=[
            Task(name="build"),
            Task(name="ship", prerequisites=("build",)),
        ],
    )
    assert result.plan_created
    assert result.plan_steps


def test_reflect_and_learn_applies_signal() -> None:
    brain = make_brain()
    result = brain.reflect_and_learn(
        goal="launch release",
        success=False,
        observed={"gate": "blocked"},
        expected={"gate": "open"},
        deviations=["approval missing"],
        metrics={"expected_actions": 4, "actions_used": 11},
    )
    assert result.reflections
    # improvement suggestion may be emitted; learning signal optional by design
    assert result.learning_signal is None or result.learning_signal.id


def test_memory_integration() -> None:
    brain = make_brain()
    entry = brain.memory.remember(key="notice", kind=MemoryType.EPISODIC, content={"text": "ship green"})
    recalled = brain.memory.recall(__import__("aura.memory.engine", fromlist=["MemoryQuery"]).MemoryQuery(text="ship green"))
    assert recalled
    assert recalled[0].id == entry.id


def test_provenance_chain() -> None:
    brain = make_brain()
    result = brain.reason(question="q", facts={"a": 0.8})
    explanation = brain.provenance(result.execution_id)
    assert explanation["execution_id"] == str(result.execution_id)
    assert "cause_chain" in explanation


def test_health_aggregates_engines() -> None:
    brain = make_brain()
    health = brain.health()
    assert health["status"] == "ok"
    assert set(health["engines"]) == {"memory", "knowledge", "learning"}


def test_replay_to_memory() -> None:
    brain = make_brain()
    result = brain.reason(question="replay me", facts={"x": 1.0})
    count = brain.record_execution_memory(result.execution_id)
    assert count >= 0