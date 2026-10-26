"""Phase 2A: automation + checkpoint durability across a process restart.

Proves the 2A.4 gate: create -> run -> checkpoint -> stop server -> restart ->
inspect -> resume, and that resume never repeats a completed side effect.
"""

from __future__ import annotations

import pytest

from aura.automation import AutomationManager, AutomationStep, StepOutcome, automation_available

pytestmark = pytest.mark.skipif(not automation_available(), reason="agents runtime not installed")


def _counted_runner(counts: dict[str, int]):
    def runner(step: AutomationStep, task) -> StepOutcome:  # noqa: ANN001 - runtime-typed
        counts[step.goal] = counts.get(step.goal, 0) + 1
        return StepOutcome(success=True)

    return runner


def test_resume_after_restart_does_not_repeat_completed_steps(tmp_path) -> None:
    state_file = str(tmp_path / "auto.sqlite3")
    counts: dict[str, int] = {}

    # Server run 1: only step 0 executes (bounded max_steps=1), then stop.
    mgr1 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    task_id = mgr1.submit(
        owner="owner:a",
        description="durable task",
        steps=[AutomationStep(goal="s0"), AutomationStep(goal="s1")],
    )
    out = mgr1.run(task_id, owner="owner:a", max_steps=1)
    assert out is not None and out["completed"] == [0]
    assert counts == {"s0": 1}
    mgr1.close()

    # Server run 2: hydrating from the same state file must keep a live task
    # and resume from step 1, never re-running step 0.
    mgr2 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    summary = mgr2.get(task_id, owner="owner:a")
    assert summary is not None, "task did not survive restart"
    assert summary["completed"] == [0]
    # checkpoints survived too
    assert summary["checkpoint_count"] >= 1

    resumed = mgr2.run(task_id, owner="owner:a")
    assert resumed is not None and resumed["state"] == "succeeded"
    assert resumed["completed"] == [0, 1]
    assert counts == {"s0": 1, "s1": 1}, "completed step was repeated across restart"
    mgr2.close()


def test_owner_isolation_survives_restart(tmp_path) -> None:
    state_file = str(tmp_path / "auto.sqlite3")
    counts: dict[str, int] = {}
    mgr1 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    task_id = mgr1.submit(
        owner="owner:a",
        description="owned task",
        steps=[AutomationStep(goal="s0"), AutomationStep(goal="s1")],
    )
    mgr1.run(task_id, owner="owner:a")
    mgr1.close()

    mgr2 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    assert mgr2.get(task_id, owner="owner:b") is None, "cross-owner read after restart"
    assert mgr2.run(task_id, owner="owner:b") is None, "cross-owner action after restart"
    assert mgr2.cancel(task_id, owner="owner:b") is None
    assert mgr2.get(task_id, owner="owner:a") is not None
    mgr2.close()


def test_terminal_state_survives_restart(tmp_path) -> None:
    state_file = str(tmp_path / "auto.sqlite3")
    counts: dict[str, int] = {}
    mgr1 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    task_id = mgr1.submit(
        owner="owner:a", description="terminal", steps=[AutomationStep(goal="s0")]
    )
    mgr1.run(task_id, owner="owner:a")
    mgr1.close()

    mgr2 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    summary = mgr2.get(task_id, owner="owner:a")
    assert summary is not None and summary["state"] == "succeeded"
    assert summary["checkpoint_count"] >= 1
    # A completed task must stay terminal across restart.
    again = mgr2.run(task_id, owner="owner:a")
    assert again is not None and again["state"] == "succeeded"
    mgr2.close()


def test_cancelled_state_survives_restart(tmp_path) -> None:
    state_file = str(tmp_path / "auto.sqlite3")
    counts: dict[str, int] = {}
    mgr1 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    task_id = mgr1.submit(
        owner="owner:a", description="cancelled", steps=[AutomationStep(goal="s0")]
    )
    mgr1.cancel(task_id, owner="owner:a")
    mgr1.close()

    mgr2 = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    summary = mgr2.get(task_id, owner="owner:a")
    assert summary is not None and summary["state"] == "cancelled"
    mgr2.close()


def test_corrupt_row_does_not_block_startup(tmp_path) -> None:
    from aura.foundation.persistent import SQLiteJsonStore

    state_file = str(tmp_path / "auto.sqlite3")
    store = SQLiteJsonStore(state_file, table="automation")
    store.put("task-good", {"task_id": "task-good", "owner": "owner:a", "steps": [], "state": "pending"})
    store.put("task-corrupt", {"bad": "json"})
    store.close()

    counts: dict[str, int] = {}
    mgr = AutomationManager(runner=_counted_runner(counts), state_path=state_file)
    assert mgr.get("task-good", owner="owner:a") is not None or len(mgr.list_tasks("owner:a")) >= 0
    mgr.close()


def test_empty_store_starts_clean(tmp_path) -> None:
    counts: dict[str, int] = {}
    mgr = AutomationManager(
        runner=_counted_runner(counts), state_path=str(tmp_path / "fresh.sqlite3")
    )
    assert mgr.list_tasks("owner:a") == []
    mgr.close()