"""Canonical automation + long-running task capability (Phase 1K).

This module is the canonical orchestration layer that turns the existing
task / agent / planning / execution / cancellation / research / verification /
reflection / learning infrastructure into a bounded, checkpointable,
resumable, cancellable long-running task capability.

It is deliberately NOT a new subsystem. Every hard mechanic is REUSED:

- lifecycle: the runtime's ``ExecutionState``/``StateMachine`` (validated
  transitions + history) from ``aura_agent.contracts.states``;
- budgets: ``AgentBudget``/``BudgetEngine`` (time/actions/retries/...) from
  ``aura_agent.budgets``;
- failure + retry: ``FailureClass``/``RetryPolicy``/``RecoveryEngine`` from
  ``aura_agent.recovery``;
- loop control: ``LoopController`` from ``aura_agent.loop_control``;
- autonomy: ``AutonomyEngine``/``AutonomyMode`` from ``aura_agent.autonomy``;
- cancellation: the canonical :class:`~aura.foundation.cancellation.CancellationTokenSource`;
- execution: the canonical agent bridge (:func:`aura.agents.run_agent_task`).

State-model mapping (reusing the runtime's states rather than adding new ones,
per the no-parallel-architecture rule):

- queued            -> PENDING / READY
- running           -> RUNNING
- paused            -> WAITING   (the runtime's supported suspended state)
- budget/loop stop  -> BLOCKED   (honest terminal, never a fake retry)
- cancelling/cancel -> CANCELLED
- done / failed     -> SUCCEEDED / FAILED

A task is a sequence of :class:`AutomationStep`; each step executes one bounded
unit of work (a canonical agent goal). A checkpoint captures exactly which
steps completed (and nothing secret), so resume is deterministic, idempotent
and never repeats completed side effects.
"""

from __future__ import annotations

import contextlib
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aura.foundation.cancellation import CancellationToken, CancellationTokenSource
from aura.foundation.errors import CancelledError

# ---------------------------------------------------------------------------
# Existence / availability (matches the agent bridge pattern)
# ---------------------------------------------------------------------------

_AGENTS_INSTALLED = False
try:
    import aura_agent  # noqa: F401

    _AGENTS_INSTALLED = True
except ImportError:  # pragma: no cover - optional runtime dependency
    _AGENTS_INSTALLED = False


def automation_available() -> bool:
    """True when the optional agent runtime (which supplies the lifecycle,
    budget, recovery and loop-control primitives) is installed."""
    return _AGENTS_INSTALLED


class AutomationUnavailableError(RuntimeError):
    """Raised when the automation layer is used without the agent runtime."""


def _runtime() -> Any:
    if not _AGENTS_INSTALLED:
        raise AutomationUnavailableError(
            "the AURA agents runtime is not installed; automation requires it"
        )
    import aura_agent  # noqa: F401

    return aura_agent


# ---------------------------------------------------------------------------
# Failure classification (authoritative enum values reused from the runtime)
# ---------------------------------------------------------------------------

_FAILURE_TRANSIENT = "transient"
_FAILURE_TIMEOUT = "timeout"
_FAILURE_PERMANENT = "permanent"
_FAILURE_POLICY = "policy"
_FAILURE_RESOURCE = "resource"
_FAILURE_VALIDATION = "validation"
_FAILURE_STATE_MISMATCH = "state_mismatch"
_FAILURE_UNKNOWN = "unknown"

#: Non-retryable by policy. Retrying a denial, invalid input or an approval
#: requirement is never safe; they abort (fail) / block (resource) instead.
_NOT_RETRYABLE = frozenset(
    {_FAILURE_POLICY, _FAILURE_VALIDATION, _FAILURE_PERMANENT, _FAILURE_STATE_MISMATCH}
)


@dataclass(frozen=True)
class StepOutcome:
    """One step's result produced by the executor (the runner)."""

    success: bool
    result: dict[str, Any] | None = None
    failure_class: str = _FAILURE_UNKNOWN
    error: str = ""
    cancelled: bool = False


@dataclass(frozen=True)
class AutomationStep:
    """One bounded unit of long-running work.

    ``goal`` is executed through the canonical agent bridge. ``capabilities``
    and ``allow_rules`` are only ever supplied by trusted caller code (the
    server never accepts them from the client). ``idempotency_key`` lets the
    executor deduplicate side effects on resume.
    """

    goal: str
    success_criteria: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    allow_rules: tuple[tuple[str, str], ...] = ()
    require_research: bool = False
    research_claims: tuple[str, ...] = ()
    idempotency_key: str | None = None
# ---------------------------------------------------------------------------
# Lifecycle mapping helpers
# ---------------------------------------------------------------------------

#: User-facing phase label derived from the authoritative runtime state.
_PHASE_BY_STATE: dict[str, str] = {
    "pending": "queued",
    "ready": "queued",
    "running": "running",
    "waiting": "paused",
    "blocked": "blocked",
    "succeeded": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
    "recovering": "recovering",
    "rolled_back": "rolled_back",
}


def _phase(state_value: str) -> str:
    return _PHASE_BY_STATE.get(state_value, state_value)


# ---------------------------------------------------------------------------
# Automation task
# ---------------------------------------------------------------------------


@dataclass
class AutomationTask:
    """A registered long-running task and its authoritative lifecycle.

    The hard lifecycle is owned by the runtime's ``StateMachine`` which is
    created lazily and stored in ``base_task``; ``state`` mirrors its value for
    cheap, lock-free reads. The task adds canonical pairing with a cancellation
    token, the step plan, retry accounting and audit-able history.
    """

    task_id: str
    owner: str
    description: str
    kind: str
    steps: tuple[AutomationStep, ...]
    source: CancellationTokenSource
    created_at: float
    # lazy-constructed runtime lifecycle handles (see AutomationManager)
    state_machine: Any = None
    budget: Any = None
    recovery: Any = None
    loop: Any = None
    autonomy: Any = None
    # keep the runtime ExecutionId for budget/recovery reuse
    execution_id: Any = None
    state: str = "pending"
    current_step: int = 0
    completed: tuple[int, ...] = ()
    attempts: dict[int, int] = field(default_factory=dict)
    results: dict[int, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    failure_class: str | None = None
    failure_reason: str = ""
    cancelled_stage: str | None = None
    finished_at: float | None = None
    #: durable copy of the resource budgets (empty by default) so a restarted
    #: manager can re-attach the same limits. Never stores secrets.
    budget_limits: dict[str, Any] | None = None

    @property
    def token(self) -> CancellationToken:
        return self.source.token

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    def next_step_index(self) -> int | None:
        for idx in range(len(self.steps)):
            if idx not in self.completed:
                return idx
        return None

    def summary(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "owner": self.owner,
            "description": self.description,
            "kind": self.kind,
            "state": self.state,
            "phase": _phase(self.state),
            "current_step": len(self.completed),
            "total_steps": self.total_steps,
            "completed": list(self.completed),
            "cancelled": self.source.token.cancelled,
            "cancelled_stage": self.cancelled_stage,
            "attempts": dict(self.attempts),
            "failure_class": self.failure_class,
            "failure_reason": self.failure_reason,
            "checkpoint_count": len(self.checkpoints),
            "event_count": len(self.events),
            "created_at": round(self.created_at, 3),
            "finished_at": round(self.finished_at, 3) if self.finished_at is not None else None,
        }

    def snapshot(self) -> dict[str, Any]:
        """Durable, secret-free serialisation for restart survival.

        Only long-lived identifiers and the observable lifecycle are captured;
        the live runtime handles (state machine, budget, loop, tokens) are
        intentionally excluded and rebuilt on restore.
        """
        return {
            "task_id": self.task_id,
            "owner": self.owner,
            "description": self.description,
            "kind": self.kind,
            "steps": [dict(step.__dict__) for step in self.steps],
            "state": self.state,
            "current_step": self.current_step,
            "completed": list(self.completed),
            "attempts": {str(k): v for k, v in self.attempts.items()},
            "results": {str(k): v for k, v in self.results.items()},
            "events": self.events,
            "checkpoints": self.checkpoints,
            "failure_class": self.failure_class,
            "failure_reason": self.failure_reason,
            "cancelled_stage": self.cancelled_stage,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "budget_limits": self.budget_limits,
            "execution_id": str(self.execution_id) if self.execution_id is not None else None,
        }

    @classmethod
    def restore(cls, snap: dict[str, Any], *, clock: Callable[[], float]) -> AutomationTask:
        """Rebuild a task from a durable snapshot (a fresh, resumable runtime).

        ``completed`` is preserved verbatim so a resumed run never repeats
        completed side effects; ``source`` is a fresh (uncancelled) token because
        a restarted process must not inherit a stale cancellation.
        """
        from aura_agent.contracts.ids import ExecutionId

        steps = tuple(AutomationStep(**s) for s in snap.get("steps", []))
        task = cls(
            task_id=snap["task_id"],
            owner=snap["owner"],
            description=snap.get("description", "automation task"),
            kind=snap.get("kind", "agent"),
            steps=steps,
            source=CancellationTokenSource(),
            created_at=snap.get("created_at") or clock(),
            execution_id=ExecutionId(snap["execution_id"]) if snap.get("execution_id") else None,
            state=snap.get("state", "pending"),
            current_step=snap.get("current_step", 0),
            completed=tuple(snap.get("completed", [])),
            attempts={int(k): v for k, v in snap.get("attempts", {}).items()},
            results={int(k): v for k, v in snap.get("results", {}).items()},
            events=list(snap.get("events", [])),
            checkpoints=list(snap.get("checkpoints", [])),
            failure_class=snap.get("failure_class"),
            failure_reason=snap.get("failure_reason", ""),
            cancelled_stage=snap.get("cancelled_stage"),
            finished_at=snap.get("finished_at"),
            budget_limits=snap.get("budget_limits"),
        )
        return task
# ---------------------------------------------------------------------------
# Automation manager
# ---------------------------------------------------------------------------


class AutomationManager:
    """Thread-safe registry + lifecycle controller for long-running tasks.

    ``runner`` is ``runner(step, task) -> StepOutcome``; it is supplied by
    trusted caller code (the API wires it to the canonical agent bridge). Tests
    inject deterministic runners. Everything else -- lifecycle, budgets,
    retries, loop control, cancellation -- is handled here by composing the
    runtime's primitives, never by reimplementing them.
    """

    def __init__(
        self,
        *,
        runner: Callable[[AutomationStep, AutomationTask], StepOutcome] | None = None,
        max_history: int = 500,
        clock: Callable[[], float] = time.monotonic,
        state_path: str | None = None,
    ) -> None:
        if runner is None:
            raise TypeError("AutomationManager requires a runner callable")
        self._runner = runner
        self._clock = clock
        self._tasks: dict[str, AutomationTask] = {}
        self._history: list[dict[str, Any]] = []
        self._max_history = max_history
        self._locks: dict[str, threading.RLock] = {}
        self._register_lock = threading.RLock()
        self._closed = False
        # Phase 2A durable persistence: an optional SQLite-backed snapshot store
        # so tasks/checkpoints survive a process restart. Never stores secrets.
        self._store = None
        if state_path:
            from aura.foundation.persistent import SQLiteJsonStore

            self._store = SQLiteJsonStore(state_path, table="automation")
            self._hydrate()

    def _hydrate(self) -> None:
        """Reload durable task snapshots into a fresh manager on startup."""
        if self._store is None:
            return
        for snap in self._store.load_all().values():
            try:
                task = AutomationTask.restore(snap, clock=self._clock)
                self._wire_runtime(task, budget_limits=snap.get("budget_limits"))
                # Keep the persisted lifecycle value authoritative; the fresh
                # state machine simply starts at READY for resummability.
                task.state = snap.get("state", "pending")
            except Exception:  # noqa: BLE001 - a corrupt row must not block startup
                continue
            with self._register_lock:
                self._tasks[task.task_id] = task
                self._locks.setdefault(task.task_id, threading.RLock())

    def _persist(self, task: AutomationTask) -> None:
        if self._store is not None:
            with contextlib.suppress(Exception):  # persistence must not crash orchestration
                self._store.put(task.task_id, task.snapshot())

    def submit(
        self,
        *,
        owner: str,
        description: str,
        steps: list[AutomationStep] | tuple[AutomationStep, ...],
        budget_limits: dict[str, float] | None = None,
    ) -> str:
        if self._closed:
            raise RuntimeError("automation manager is closed")
        if not owner:
            raise ValueError("owner is required")
        if not steps:
            raise ValueError("at least one automation step is required")
        _runtime()
        from aura_agent.contracts.ids import ExecutionId

        suffix = uuid.uuid4().hex[:16]
        task_id = f"task-{suffix}"
        task = AutomationTask(
            task_id=task_id,
            owner=owner,
            description=description or "automation task",
            kind="agent",
            steps=tuple(steps),
            source=CancellationTokenSource(),
            created_at=self._clock(),
            execution_id=ExecutionId(f"exe-{suffix}"),
        )
        self._wire_runtime(task, budget_limits=budget_limits)
        with self._register_lock:
            self._tasks[task_id] = task
            self._locks.setdefault(task_id, threading.RLock())
        self._record_event(task, "task.submitted", {"steps": len(steps), "owner": owner})
        self._persist(task)
        return task_id

    def _wire_runtime(self, task: AutomationTask, *, budget_limits: dict[str, float] | None) -> None:
        from aura_agent.budgets.budget_engine import BudgetEngine
        from aura_agent.budgets.models.agent_budget import AgentBudget
        from aura_agent.contracts.states import ExecutionState, StateMachine
        from aura_agent.loop_control.loop_controller import LoopController
        from aura_agent.recovery.recovery_engine import RecoveryEngine

        sm = StateMachine()
        sm.transition(ExecutionState.READY, reason="queued")  # PENDING -> READY
        task.state_machine = sm
        task.state = sm.state.value
        task.budget = BudgetEngine()
        task.budget.attach(task.execution_id, AgentBudget(limits=dict(budget_limits or {"actions": 16})))
        task.budget_limits = dict(budget_limits or {"actions": 16})
        task.recovery = RecoveryEngine()
        # Safety net above the bounded retry budget: retry exhausts -> FAILED,
        # and loop control would only fire if something bypasses the retry cap.
        task.loop = LoopController(max_repetitions=5)

    def _record_event(self, task: AutomationTask, event: str, payload: dict[str, Any]) -> None:
        task.events.append(
            {"event": event, "payload": payload, "at": datetime.now(UTC).isoformat()}
        )
# -- access --------------------------------------------------------------

    def _lock_for(self, task_id: str) -> threading.RLock:
        return self._locks.setdefault(task_id, threading.RLock())

    def _owner_ok(self, task: AutomationTask, owner: str) -> bool:
        return task.owner == owner

    def get(self, task_id: str, *, owner: str) -> dict[str, Any] | None:
        task = self._tasks.get(task_id)
        if task is None or not self._owner_ok(task, owner):
            return None
        return task.summary()

    def list_tasks(self, owner: str) -> list[dict[str, Any]]:
        out = [t.summary() for t in self._tasks.values() if t.owner == owner]
        out.sort(key=lambda s: s["created_at"])
        return out

    def _set_state(self, task: AutomationTask, target: str, *, reason: str = "") -> bool:
        """Perform a validated transition on the task's state machine (reuse)."""
        sm = task.state_machine
        if sm is None:
            return False
        from aura_agent.contracts.states import ExecutionState

        try:
            enum_target = ExecutionState(target)
        except ValueError:
            return False
        if sm.state is enum_target:
            return True
        if not sm.can_transition(enum_target):
            return False
        sm.transition(enum_target, reason=reason)
        task.state = sm.state.value
        self._record_event(task, "task.transition", {"to": task.state, "reason": reason})
        self._persist(task)
        return True

    def run(
        self,
        task_id: str,
        *,
        owner: str,
        max_steps: int = 0,
        token: CancellationToken | None = None,
    ) -> dict[str, Any] | None:
        """Drive a task to a terminal or paused state by advancing steps.

        Cooperative: stops on pause (WAITING), cancellation, budget/loop block
        or completion. ``max_steps == 0`` means run until terminal/paused.
        """
        guard = token or CancellationToken()
        executed = 0
        while True:
            if guard.cancelled:
                self.cancel(task_id, owner=owner)
                break
            if self._closed:
                break
            with self._lock_for(task_id):
                task = self._tasks.get(task_id)
                if task is None or not self._owner_ok(task, owner):
                    return None
                if task.state in {"succeeded", "failed", "cancelled", "blocked", "waiting"}:
                    break
                if task.state in {"pending", "ready", "running"}:
                    self.advance(task_id, owner=owner)
                    executed += 1
                    if max_steps and executed >= max_steps:
                        break
        return self.get(task_id, owner=owner)
# -- core step engine ----------------------------------------------------

    def advance(self, task_id: str, *, owner: str) -> dict[str, Any] | None:
        """Run exactly one pending step, then return the latest summary.

        The caller (a worker loop or the API) re-invokes ``advance``/``run`` to
        move the task forward. Cooperative: cancellation, budget and loop
        checks all happen before a step is executed.
        """
        with self._lock_for(task_id):
            task = self._tasks.get(task_id)
            if task is None or not self._owner_ok(task, owner):
                return None
            if task.state in {"succeeded", "failed", "cancelled", "blocked"}:
                return task.summary()
            if task.state == "waiting":
                return task.summary()  # paused; hold until resume()
            if task.state_machine is None:
                return task.summary()
            if task.source.token.cancelled:
                self._finish_cancelled(task, "orchestration")
                return task.summary()

            step_idx = task.next_step_index()
            if step_idx is None:
                self._finish_succeeded(task)
                return task.summary()

            if not self._budget_ok(task):
                self._finish_blocked(task, "budget exceeded")
                return task.summary()

            # loop control: repeated identical attempts trigger a hard stop.
            signature = f"step:{step_idx}"
            loop = task.loop
            if loop is not None:
                signals = loop.record(signature)
                if signals:
                    self._finish_blocked(task, f"loop detected: {signals[0].detail}")
                    return task.summary()

            self._set_state(task, "running", reason=f"start step {step_idx}")

            # advance from READY/WAITING into RUNNING requires a valid runtime
            # transition; _set_state handles the mapping.
            step = task.steps[step_idx]
            self._record_event(task, "step.start", {"index": step_idx, "goal": step.goal})

            try:
                outcome = self._runner(step, task)
            except CancelledError:
                self._finish_cancelled(task, f"step {step_idx}")
                return task.summary()
            except Exception as exc:  # noqa: BLE001 - classify, never crash
                outcome = StepOutcome(
                    success=False,
                    failure_class=_FAILURE_PERMANENT,
                    error=f"{type(exc).__name__}: {exc}",
                )

            self._charge(task)

            if outcome.cancelled or task.source.token.cancelled:
                self._finish_cancelled(task, f"step {step_idx}")
                return task.summary()

            if outcome.success:
                task.completed = tuple(sorted((*task.completed, step_idx)))
                task.results[step_idx] = outcome.result or {}
                self._record_event(task, "step.complete", {"index": step_idx})
                self._checkpoint(task, reason=f"completed step {step_idx}")
                if task.next_step_index() is None:
                    self._finish_succeeded(task)
                return task.summary()

            # failure -> classify / retry via the reused recovery engine.
            return self._handle_failure(task, step, step_idx, outcome)

    def _handle_failure(
        self, task: AutomationTask, step: AutomationStep, step_idx: int, outcome: StepOutcome
    ) -> dict[str, Any]:
        cls = outcome.failure_class if outcome.failure_class in {
            _FAILURE_TRANSIENT, _FAILURE_TIMEOUT, _FAILURE_PERMANENT, _FAILURE_POLICY,
            _FAILURE_RESOURCE, _FAILURE_VALIDATION, _FAILURE_STATE_MISMATCH, _FAILURE_UNKNOWN,
        } else _FAILURE_UNKNOWN

        attempts = task.attempts.get(step_idx, 0) + 1
        task.attempts[step_idx] = attempts
        self._record_event(
            task, "step.failed",
            {"index": step_idx, "failure_class": cls, "attempts": attempts, "error": outcome.error},
        )

        # safety-gate: never auto-retry denials / invalid input / missing approval.
        if cls in _NOT_RETRYABLE:
            self._finish_blocked(task, outcome.error or f"not retryable ({cls})") if cls == _FAILURE_RESOURCE else None
            if cls == _FAILURE_RESOURCE:
                self._finish_blocked(task, outcome.error or "budget/resource exhausted")
            else:
                self._finish_failed(task, cls, outcome.error or f"denied/invalid ({cls})")
            return task.summary()

        # transient -> bounded retry via the reused recovery engine.
        try:
            from aura_agent.recovery.models import RecoveryRequest, RetryPolicy
        except Exception:  # pragma: no cover
            self._finish_failed(task, cls, outcome.error or "recovery unavailable")
            return task.summary()

        decision = task.recovery.decide(
            RecoveryRequest(
                execution_id=task.execution_id,
                goal_id=None,
                tool_name=f"automation.step.{step_idx}",
                failure_class=_to_runtime_failure_class(cls),
                attempts=attempts - 1,
                error=outcome.error,
                retry_policy=RetryPolicy(max_retries=2, backoff_s=0.0),
            )
        )
        if decision.should_retry:
            self._record_event(task, "step.retry", {"index": step_idx, "attempts": attempts})
            # stay RUNNING; the next advance() re-attempts this same step.
            return task.summary()

        # recovery decided to abort (retry budget exhausted / permanent).
        self._finish_failed(task, cls, outcome.error or f"unrecoverable ({cls})")
        return task.summary()
# -- budget / checkpoint / finish helpers --------------------------------

    def _budget_ok(self, task: AutomationTask) -> bool:
        """Read-only budget check before running one more step (reuse BudgetEngine).

        Enforces both the action/iteration budget (via the runtime BudgetEngine)
        and, when configured, the ``time_s`` budget against the task start time.
        """
        if task.budget is None:
            return True
        try:
            budget = task.budget.acquire(task.execution_id)
            if budget is not None:
                time_limit = budget.limit("time_s")
                if time_limit < float("inf") and (self._clock() - task.created_at) >= time_limit:
                    return False
            decision = task.budget.check_execution(task.execution_id, {"actions": 1.0})
            return bool(decision.allowed)
        except Exception:  # pragma: no cover - fail closed
            return False

    def _charge(self, task: AutomationTask) -> None:
        """Account one executed step against the task budget (reuse)."""
        if task.budget is None:
            return
        import contextlib

        with contextlib.suppress(Exception):  # budget charge must not crash orchestration
            task.budget.consume(task.execution_id, dimension="actions", amount=1.0)

    def _checkpoint(self, task: AutomationTask, *, reason: str = "") -> None:
        task.checkpoints.append(
            {
                "task_id": task.task_id,
                "state": task.state,
                "completed": list(task.completed),
                "attempts": dict(task.attempts),
                "reason": reason,
                "captured_at": datetime.now(UTC).isoformat(),
                "provenance": {
                    "owner": task.owner,
                    "kind": task.kind,
                    "cancellation": task.source.token.cancelled,
                },
            }
        )
        self._persist(task)

    def _finish_succeeded(self, task: AutomationTask) -> None:
        task.finished_at = self._clock()
        self._set_state(task, "succeeded", reason="all steps completed")
        self._archive(task)

    def _finish_failed(self, task: AutomationTask, cls: str, reason: str) -> None:
        task.failure_class = cls
        task.failure_reason = reason
        task.finished_at = self._clock()
        self._set_state(task, "failed", reason=reason)
        self._archive(task)

    def _finish_blocked(self, task: AutomationTask, reason: str) -> None:
        task.failure_class = _FAILURE_RESOURCE
        task.failure_reason = reason
        task.finished_at = self._clock()
        self._set_state(task, "blocked", reason=reason)
        self._archive(task)

    def _finish_cancelled(self, task: AutomationTask, stage: str) -> None:
        task.cancelled_stage = task.cancelled_stage or stage
        task.finished_at = self._clock()
        self._set_state(task, "cancelled", reason=f"cancelled at {stage}")

    def _archive(self, task: AutomationTask) -> None:
        with self._register_lock:
            self._history.append(task.summary())
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
# -- control -------------------------------------------------------------

    def pause(self, task_id: str, *, owner: str) -> dict[str, Any] | None:
        with self._lock_for(task_id):
            task = self._tasks.get(task_id)
            if task is None or not self._owner_ok(task, owner):
                return None
            if task.state == "running":
                self._set_state(task, "waiting", reason="paused by owner")
                self._record_event(task, "task.paused", {})
            return task.summary()

    def resume(self, task_id: str, *, owner: str) -> dict[str, Any] | None:
        with self._lock_for(task_id):
            task = self._tasks.get(task_id)
            if task is None or not self._owner_ok(task, owner):
                return None
            if task.state == "waiting":
                self._set_state(task, "running", reason="resumed by owner")
                self._record_event(task, "task.resumed", {})
            return task.summary()

    def cancel(self, task_id: str, *, owner: str) -> dict[str, Any] | None:
        """Cancel a task, reaching the active step immediately.

        The token is cancelled outside the per-task lock on purpose: ``cancel``
        must not wait behind a long-running step, so the running step observes
        the cancellation and cooperatively stops. The terminal state is then
        finalised under the lock (a no-op if the step already finished).
        """
        task = self._tasks.get(task_id)
        if task is None or not self._owner_ok(task, owner):
            return None
        task.source.cancel()  # thread-safe; reaches the active step
        with self._lock_for(task_id):
            if task.state not in {"succeeded", "failed", "cancelled", "blocked"}:
                self._finish_cancelled(task, "orchestration")
        return task.summary()

    def retry(
        self,
        task_id: str,
        *,
        owner: str,
        step: int | None = None,
    ) -> dict[str, Any] | None:
        """Request a bounded re-run of a failed task.

        Only a *failed* task (a resolved, non-resource failure) may be retried;
        a cancellations or budget/loop ``blocked`` task is never silently
        retried. Retry re-enters a fresh lifecycle for the target step on an
        explicit owner-authorized call, preserves prior provenance in the event
        log, and re-runs only the target step (idempotent -- completed steps are
        never repeated).
        """
        with self._lock_for(task_id):
            task = self._tasks.get(task_id)
            if task is None or not self._owner_ok(task, owner):
                return None
            if task.state != "failed":
                return task.summary()
            target = step if step is not None else max(task.completed, default=-1) + 1
            if target < 0 or target >= task.total_steps:
                return task.summary()
            prior = {"state": task.state, "failure_class": task.failure_class, "failure_reason": task.failure_reason}
            # explicit re-entry: rebuild a fresh lifecycle for the new attempt.
            from aura_agent.contracts.states import ExecutionState, StateMachine

            task.completed = tuple(c for c in task.completed if c != target)
            task.attempts.pop(target, None)
            task.failure_class = None
            task.failure_reason = ""
            task.finished_at = None
            fresh = StateMachine()
            fresh.transition(ExecutionState.READY, reason="queued for retry")
            task.state_machine = fresh
            task.state = fresh.state.value
            loop = task.loop
            if loop is not None and hasattr(loop, "reset"):
                loop.reset()
            self._record_event(task, "task.retry", {"step": target, "owner": owner, "prior": prior})
            self._persist(task)
            return task.summary()

    def checkpoints(self, task_id: str, *, owner: str) -> list[dict[str, Any]] | None:
        with self._lock_for(task_id):
            task = self._tasks.get(task_id)
            if task is None or not self._owner_ok(task, owner):
                return None
            return list(task.checkpoints)

    def close(self) -> None:
        self._closed = True
        with self._register_lock:
            for task in self._tasks.values():
                if not task.source.token.cancelled:
                    task.source.cancel()


def _to_runtime_failure_class(value: str) -> Any:
    """Map our internal failure string to the runtime's FailureClass enum."""
    from aura_agent.recovery.models import FailureClass

    return {
        "transient": FailureClass.TRANSIENT,
        "timeout": FailureClass.TIMEOUT,
        "permanent": FailureClass.PERMANENT,
        "policy": FailureClass.POLICY,
        "resource": FailureClass.RESOURCE,
        "validation": FailureClass.VALIDATION,
        "state_mismatch": FailureClass.STATE_MISMATCH,
        "unknown": FailureClass.UNKNOWN,
    }.get(value, FailureClass.UNKNOWN)


__all__ = [
    "AutomationManager",
    "AutomationStep",
    "AutomationTask",
    "AutomationUnavailableError",
    "StepOutcome",
    "automation_available",
]