"""Phase 1K tests: canonical automation / long-running task manager.

Covers lifecycle transitions (valid + invalid), owner isolation, cancellation,
pause/resume, checkpoint + resume idempotency, bounded retries, budget
exhaustion, blocked actions, provenance and concurrent/clean-up behaviour.
"""

from __future__ import annotations

import threading

import pytest

from aura.automation import (
    AutomationManager,
    AutomationStep,
    StepOutcome,
    automation_available,
)

pytestmark = pytest.mark.skipif(not automation_available(), reason="agents runtime not installed")


def _ok(goal: str = "g") -> AutomationStep:
    return AutomationStep(goal, capabilities=("echo",))


def _ok_runner(step: AutomationStep, task) -> StepOutcome:
    return StepOutcome(success=True, result={"goal": step.goal})


# -- lifecycle ----------------------------------------------------------------


def test_submit_is_queued_then_run_completes() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="multi", steps=[_ok("a"), _ok("b"), _ok("c")])
    s = m.get(tid, owner="alice")
    assert s is not None
    assert s["phase"] == "queued"
    final = m.run(tid, owner="alice")
    assert final["state"] == "succeeded"
    assert final["phase"] == "completed"
    assert final["completed"] == [0, 1, 2]
    assert final["checkpoint_count"] == 3


def test_invalid_step_count_rejected() -> None:
    m = AutomationManager(runner=_ok_runner)
    with pytest.raises(ValueError):
        m.submit(owner="alice", description="x", steps=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        m.submit(owner="", description="x", steps=[_ok()])  # type: ignore[arg-type]


def test_advance_paused_never_runs() -> None:
    calls: list[str] = []

    def runner(step, task) -> StepOutcome:
        calls.append(step.goal)
        return StepOutcome(success=True)

    m = AutomationManager(runner=runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a"), _ok("b")])
    m.advance(tid, owner="alice")  # completes step 0
    paused = m.pause(tid, owner="alice")
    assert paused["state"] == "waiting"
    assert paused["phase"] == "paused"
    m.advance(tid, owner="alice")  # must not run a step while paused
    m.advance(tid, owner="alice")
    assert calls == ["a"]


def test_pause_resume_cycle() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a"), _ok("b")])
    m.pause(tid, owner="alice")  # queued, not running -> no-op
    assert m.get(tid, owner="alice")["phase"] == "queued"
    m.advance(tid, owner="alice")  # completes "a", still running
    assert m.pause(tid, owner="alice")["phase"] == "paused"
    resumed = m.resume(tid, owner="alice")
    assert resumed["state"] == "running"
    final = m.run(tid, owner="alice")
    assert final["state"] == "succeeded"
# -- cancellation -------------------------------------------------------------


def test_cancel_mid_run_is_terminal_and_unrepeatable() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok(), _ok()])
    m.advance(tid, owner="alice")
    c = m.cancel(tid, owner="alice")
    assert c["state"] == "cancelled"
    assert c["cancelled"] is True
    assert m.retry(tid, owner="alice")["state"] == "cancelled"
    assert m.get(tid, owner="alice")["state"] == "cancelled"


def test_cancel_before_start_aborts_before_execution() -> None:
    calls: list[str] = []

    def runner(step, task) -> StepOutcome:
        calls.append(step.goal)
        return StepOutcome(success=True)

    m = AutomationManager(runner=runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a")])
    m.cancel(tid, owner="alice")
    m.run(tid, owner="alice")
    assert calls == []
    assert m.get(tid, owner="alice")["state"] == "cancelled"


# -- checkpoint / resume idempotency ------------------------------------------


def test_resume_never_repeats_completed_steps() -> None:
    ran: dict[str, int] = {}

    def runner(step, task) -> StepOutcome:
        key = step.goal
        ran[key] = ran.get(key, 0) + 1
        return StepOutcome(success=True)

    m = AutomationManager(runner=runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a"), _ok("b"), _ok("c")])
    m.advance(tid, owner="alice")  # a
    cps1 = m.checkpoints(tid, owner="alice")
    assert len(cps1) == 1 and cps1[0]["completed"] == [0]
    m.pause(tid, owner="alice")
    m.resume(tid, owner="alice")
    m.run(tid, owner="alice")  # b, c
    assert m.get(tid, owner="alice")["state"] == "succeeded"
    assert ran == {"a": 1, "b": 1, "c": 1}
    cps = m.checkpoints(tid, owner="alice")
    assert all(cp["provenance"]["owner"] == "alice" for cp in cps)
# -- retries ------------------------------------------------------------------


def test_transient_failure_retries_bounded_then_fails() -> None:
    calls: list[str] = []

    def flaky(step, task) -> StepOutcome:
        calls.append(step.goal)
        return StepOutcome(success=False, failure_class="transient", error="boom")

    m = AutomationManager(runner=flaky)
    tid = m.submit(owner="alice", description="x", steps=[_ok()])
    m.run(tid, owner="alice")
    s = m.get(tid, owner="alice")
    assert s["state"] == "failed"
    assert len(calls) <= 3  # initial + bounded retries, never infinite


def test_permanent_failure_fails_immediately_without_retry() -> None:
    calls: list[str] = []

    def perm(step, task) -> StepOutcome:
        calls.append(step.goal)
        return StepOutcome(success=False, failure_class="permanent", error="nope")

    m = AutomationManager(runner=perm)
    tid = m.submit(owner="alice", description="x", steps=[_ok()])
    m.run(tid, owner="alice")
    assert m.get(tid, owner="alice")["state"] == "failed"
    assert len(calls) == 1
    assert m.get(tid, owner="alice")["failure_class"] == "permanent"


def test_policy_denial_is_never_retried() -> None:
    calls: list[str] = []

    def denied(step, task) -> StepOutcome:
        calls.append(step.goal)
        return StepOutcome(success=False, failure_class="policy", error="capability denied")

    m = AutomationManager(runner=denied)
    tid = m.submit(owner="alice", description="x", steps=[_ok()])
    m.run(tid, owner="alice")
    assert m.get(tid, owner="alice")["state"] == "failed"
    assert len(calls) == 1


# -- budgets / blocked --------------------------------------------------------


def test_budget_exhaustion_blocks_not_fails() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(
        owner="alice",
        description="x",
        steps=[_ok("a"), _ok("b")],
        budget_limits={"actions": 1},
    )
    final = m.run(tid, owner="alice")
    assert final["state"] == "blocked"
    assert final["phase"] == "blocked"
    assert final["completed"] == [0]


def test_time_budget_exhaustion_blocks() -> None:
    now = [0.0]
    m = AutomationManager(runner=_ok_runner, clock=lambda: now[0])
    tid = m.submit(
        owner="alice",
        description="x",
        steps=[_ok("a"), _ok("b")],
        budget_limits={"time_s": 5, "actions": 100},
    )
    first = m.advance(tid, owner="alice")
    assert first["completed"] == [0]
    now[0] = 10.0  # exceed the time budget
    final = m.advance(tid, owner="alice")
    assert final["state"] == "blocked"
    assert final["completed"] == [0]


def test_blocked_task_cannot_be_retried_without_refreshing_budget() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a"), _ok("b")], budget_limits={"actions": 1})
    m.run(tid, owner="alice")
    assert m.get(tid, owner="alice")["state"] == "blocked"
    assert m.retry(tid, owner="alice")["state"] == "blocked"


def test_owner_retry_of_failed_task_resumes() -> None:
    state = {"hit": False}

    def stubborn(step, task) -> StepOutcome:
        if not state["hit"]:
            state["hit"] = True
            return StepOutcome(success=False, failure_class="permanent", error="refused once")
        return StepOutcome(success=True)

    m = AutomationManager(runner=stubborn)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a")])
    m.run(tid, owner="alice")
    assert m.get(tid, owner="alice")["state"] == "failed"
    m.retry(tid, owner="alice")
    m.run(tid, owner="alice")
    assert m.get(tid, owner="alice")["state"] == "succeeded"


# -- authorization / owner isolation / concurrency / cleanup ------------------


def test_owner_isolation() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok()])
    assert m.get(tid, owner="mallory") is None
    assert m.list_tasks("mallory") == []
    assert m.advance(tid, owner="mallory") is None
    assert m.cancel(tid, owner="mallory") is None
    assert m.pause(tid, owner="mallory") is None
    assert m.checkpoints(tid, owner="mallory") is None


def test_concurrent_tasks_are_isolated() -> None:
    m = AutomationManager(runner=_ok_runner)
    pairs = [
        (m.submit(owner=f"owner{i}", description="x", steps=[_ok() for _ in range(3)]), f"owner{i}")
        for i in range(5)
    ]
    results: list[dict] = []
    errors: list[Exception] = []

    def worker(tid: str, owner: str):
        try:
            results.append(m.run(tid, owner=owner))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(tid, owner)) for tid, owner in pairs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert all(r is not None and r["state"] == "succeeded" for r in results)


def test_close_cancels_in_flight() -> None:
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok()])
    m.close()
    assert m.get(tid, owner="alice")["cancelled"] is True
    with pytest.raises(RuntimeError):
        m.submit(owner="alice", description="x", steps=[_ok()])
# -- runtime vertical slice + cancellation during execution -------------------


def test_runtime_vertical_slice_lifecycle() -> None:
    """The directive's reference slice: create -> queue -> run -> checkpoint ->
    pause -> resume -> verify -> complete, asserting each phase honestly."""
    m = AutomationManager(runner=_ok_runner)
    tid = m.submit(owner="alice", description="slice", steps=[_ok("a"), _ok("b"), _ok("c")])
    assert m.get(tid, owner="alice")["phase"] == "queued"            # QUEUED
    m.advance(tid, owner="alice")                                     # step a
    assert m.get(tid, owner="alice")["completed"] == [0]
    assert m.get(tid, owner="alice")["checkpoint_count"] == 1          # checkpoint
    assert m.pause(tid, owner="alice")["phase"] == "paused"            # PAUSED
    m.advance(tid, owner="alice")                                       # stays paused
    assert m.get(tid, owner="alice")["completed"] == [0]
    assert m.resume(tid, owner="alice")["state"] == "running"          # resume
    final = m.run(tid, owner="alice")                                  # verify + complete
    assert final["state"] == "succeeded"
    assert final["completed"] == [0, 1, 2]
    assert len(m.checkpoints(tid, owner="alice")) >= 3


def test_cancellation_during_execution_reaches_active_step() -> None:
    import time


    def runner(step, task) -> StepOutcome:
        if step.goal == "long":
            for _ in range(200):
                if task.token.cancelled:
                    return StepOutcome(success=False, cancelled=True)
                time.sleep(0.01)
        return StepOutcome(success=True)

    m = AutomationManager(runner=runner)
    tid = m.submit(owner="alice", description="x", steps=[_ok("a"), _ok("long")])
    outcome: dict = {}

    def work():
        outcome.update(r=m.run(tid, owner="alice"))

    thread = threading.Thread(target=work)
    thread.start()
    # wait until step "a" completed, then cancel during the active long step
    deadline = time.time() + 5
    while time.time() < deadline:
        s = m.get(tid, owner="alice")
        if s is not None and s["completed"] == [0]:
            break
        time.sleep(0.02)
    m.cancel(tid, owner="alice")
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert outcome["r"]["state"] == "cancelled"
    assert outcome["r"]["cancelled"] is True