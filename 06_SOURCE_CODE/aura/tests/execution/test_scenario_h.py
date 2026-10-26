"""Scenario H — end-to-end temporary-workspace software workflow.

Drives the real canonical path (pipeline -> planning -> guardrails ->
execution engine -> secure workspace actions) over a temporary directory,
then cleans up exactly the workspace the test created. No user files are used.
"""

from __future__ import annotations

import sys
from pathlib import Path

from aura.brain.engine import BrainEngine
from aura.core.pipeline import ExecutionPipeline, PipelineRequest, default_guardrails
from aura.execution.actions import WorkspaceManager
from aura.execution.registry import ActionRegistry
from aura.planning.models import Goal, Task
from aura.security.audit import AuditLog


def test_scenario_h_temporary_workspace_vertical_slice(tmp_path: Path) -> None:
    ws_root = tmp_path / "wsroot"
    audit = AuditLog()
    manager = WorkspaceManager(workspaces_root=ws_root, audit=audit)
    registry = ActionRegistry()
    manager.install(registry)
    guardrails = default_guardrails(registry)
    pipeline = ExecutionPipeline(
        brain=BrainEngine.create(seed=3),
        registry=registry,
        guardrails=guardrails,
        audit=audit,
        max_parallel=1,
    )
    default_ws = manager.root / "default"
    assert default_ws.is_dir()

    goal = Goal.create(
        description="Build and verify a small python script in a temporary workspace",
        success_criteria=("script parses", "verifier ran"),
    )
    tasks = (
        Task(name="filesystem.mkdir", capability="filesystem.write"),
        Task(name="filesystem.write", capability="filesystem.write", prerequisites=("filesystem.mkdir",)),
        Task(name="filesystem.read", capability="filesystem.read", prerequisites=("filesystem.write",)),
        Task(
            name="process.run",
            capability="process.run",
            prerequisites=("filesystem.read",),
            estimated_cost=1.0,
            risk=0.2,
        ),
        Task(
            name="workspace.cleanup",
            capability="workspace.cleanup",
            prerequisites=("process.run",),
            estimated_cost=1.0,
            risk=0.2,
        ),
    )
    request = PipelineRequest(
        question="Produce and verify a small python script in a temporary workspace",
        claims=(),
        goal=goal,
        tasks=tasks,
        action_inputs={
            "filesystem.mkdir": {"path": "src"},
            "filesystem.write": {"path": "src/app.py", "content": "def answer():\n    return 42\n"},
            "filesystem.read": {"path": "src/app.py"},
            "process.run": {
                "command": sys.executable,
                "args": ["-c", "print('verified')"],
                "cwd": ".",
            },
            "workspace.cleanup": {"name": "default"},
        },
        approval=True,
        world={},
    )

    result = pipeline.run(request)

    # The full flow succeeded and every planned step executed in dependency order.
    assert result.success
    actions = [r.request.action for r in result.executions]
    assert actions == [
        "filesystem.mkdir",
        "filesystem.write",
        "filesystem.read",
        "process.run",
        "workspace.cleanup",
    ]
    by_action = {r.request.action: r for r in result.executions}
    assert by_action["filesystem.read"].action_result.output["content"] == "def answer():\n    return 42\n"
    assert by_action["process.run"].action_result.output["stdout"].strip() == "verified"
    assert by_action["process.run"].action_result.output["exit_code"] == 0

    # Audit captured the file + process operations.
    assert any(e.action == "workspace.write" for e in audit.entries())
    assert any(e.action == "workspace.process.run" and e.decision == "allow" for e in audit.entries())

    # The flight recorder traced the real actions (evidence preserved).
    traced_actions = {
        e.payload["action"]
        for e in pipeline.brain.recorder.events(execution_id=result.execution_id)
        if e.event_type == "pipeline.action"
    }
    assert {"filesystem.write", "process.run", "workspace.cleanup"} <= traced_actions

    # Cleanup removed exactly the workspace the test created.
    assert not default_ws.exists()


def test_scenario_h_rejected_step_marks_plan_failed(tmp_path: Path) -> None:
    """A denied step must fail the run and leave the workspace side-effect free."""
    manager = WorkspaceManager(workspaces_root=tmp_path / "wsroot", audit=AuditLog())
    registry = ActionRegistry()
    manager.install(registry)
    pipeline = ExecutionPipeline(
        brain=BrainEngine.create(seed=3),
        registry=registry,
        guardrails=default_guardrails(registry),
        max_parallel=1,
    )
    request = PipelineRequest(
        question="attempt an escaping write",
        goal=Goal.create(description="escape attempt"),
        tasks=(Task(name="filesystem.write", capability="filesystem.write"),),
        action_inputs={
            "filesystem.write": {"path": "../../escaped.txt", "content": "boom"},
        },
        approval=True,
        world={},
    )
    result = pipeline.run(request)
    assert not result.success
    assert result.executions and not result.executions[0].ok
    assert "escapes workspace" in result.executions[0].action_result.error
    assert not (tmp_path / "escaped.txt").exists()