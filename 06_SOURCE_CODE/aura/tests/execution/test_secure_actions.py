"""SRC-1 security tests for the secure workspace/filesystem/process actions.

Every operation runs through the canonical guardrail gate + execution engine
over a temporary directory tree. No user project files are touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aura.core.pipeline import default_guardrails
from aura.execution.actions import (
    MAX_OUTPUT_BYTES_DEFAULT,
    WorkspaceError,
    WorkspaceManager,
)
from aura.execution.engine import ExecutionEngine, ExecutionRequest, ExecutionResult
from aura.execution.models import ActionInputs, WorldState
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.foundation.errors import NotFoundError
from aura.security.audit import AuditLog
from aura.security.capabilities import CapabilityRegistry
from aura.security.guardrails import GuardrailService
from aura.security.permissions import PolicyEngine


@pytest.fixture
def manager(tmp_path: Path) -> WorkspaceManager:
    return WorkspaceManager(workspaces_root=tmp_path / "wsroot", audit=AuditLog())


@pytest.fixture
def registry(manager: WorkspaceManager) -> ActionRegistry:
    reg = ActionRegistry()
    manager.install(reg)
    return reg


def _executor(registry: ActionRegistry, *, allow_all: bool = True) -> ExecutionEngine:
    guardrails = default_guardrails(registry) if allow_all else GuardrailService(
        capabilities=CapabilityRegistry(), policies=PolicyEngine()
    )
    return ExecutionEngine(registry=registry, guardrails=guardrails)


def _run(
    engine: ExecutionEngine,
    action: str,
    inputs: dict[str, object],
    *,
    approval: bool = False,
    cancellation: CancellationToken | None = None,
) -> ExecutionResult:
    return engine.execute(
        ExecutionRequest(
            action=action,
            inputs=ActionInputs(values=inputs),
            world_state=WorldState(values={}),
            approval=approval,
        ),
        cancellation=cancellation,
    )


def _approved(engine: ExecutionEngine, action: str, inputs: dict[str, object]) -> ExecutionResult:
    return _run(engine, action, inputs, approval=True)


def test_valid_workspace_family_executes(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)

    made = _run(engine, "filesystem.mkdir", {"path": "src"})
    assert made.ok and made.action_result.output["path"] == "src"

    written = _run(engine, "filesystem.write", {"path": "src/app.py", "content": "print('hi')\n"})
    assert written.ok and written.action_result.output["bytes"] == len(b"print('hi')\n")

    listed = _run(engine, "filesystem.list", {"path": "src"})
    assert listed.ok and any(e["name"] == "app.py" for e in listed.action_result.output["entries"])

    read_back = _run(engine, "filesystem.read", {"path": "src/app.py"})
    assert read_back.ok and read_back.action_result.output["content"] == "print('hi')\n"

    probe = _approved(engine, "process.run", {"command": sys.executable, "args": ["-c", "print('ok')"]})
    assert probe.ok
    assert probe.action_result.output["exit_code"] == 0
    assert probe.action_result.output["stdout"].strip() == "ok"
    assert probe.action_result.output["duration_ms"] >= 0.0


def test_process_run_requires_approval(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    """Executing a process is consequential: the safety gate must demand approval."""
    engine = _executor(registry)
    denied = _run(engine, "process.run", {"command": sys.executable, "args": ["-c", "pass"]})
    assert not denied.ok
    assert "review" in denied.action_result.error.lower() or "approval" in denied.action_result.error.lower()


def test_path_traversal_rejected(manager: WorkspaceManager, registry: ActionRegistry, tmp_path: Path) -> None:
    engine = _executor(registry)
    result = _run(engine, "filesystem.write", {"path": "../escaped.txt", "content": "x"})
    assert not result.ok
    assert "escapes workspace" in result.action_result.error
    assert not (manager.root.parent / "escaped.txt").exists()  # no side effect


def test_absolute_path_outside_rejected(manager: WorkspaceManager, registry: ActionRegistry, tmp_path: Path) -> None:
    engine = _executor(registry)
    outside = tmp_path / "outside.txt"
    result = _run(engine, "filesystem.write", {"path": str(outside), "content": "x"})
    assert not result.ok
    assert "escapes workspace" in result.action_result.error
    assert not outside.exists()


def test_symlink_escape_rejected(manager: WorkspaceManager, registry: ActionRegistry, tmp_path: Path) -> None:
    import os

    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    (secret_dir / "key.txt").write_text("top-secret", encoding="utf-8")
    link_dir = manager.root / "default" / "link"
    try:
        os.symlink(secret_dir, link_dir)
    except (OSError, PermissionError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this platform")
    engine = _executor(registry)
    result = _run(engine, "filesystem.read", {"path": "link/key.txt"})
    assert not result.ok, "reading through an escaping symlink must be denied"
    assert "escapes workspace" in result.action_result.error


def test_junction_escape_rejected(manager: WorkspaceManager, registry: ActionRegistry, tmp_path: Path) -> None:
    """NTFS junction escape (no symlink privilege required) uses the same
    Path.resolve() confinement path and must be rejected identically (P44)."""
    import subprocess

    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    (secret_dir / "key.txt").write_text("top-secret", encoding="utf-8")
    link = manager.root / "default" / "jlink"
    r = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(secret_dir)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        pytest.skip("junction creation unavailable on this platform")
    engine = _executor(registry)
    result = _run(engine, "filesystem.read", {"path": "jlink/key.txt"})
    assert not result.ok, "reading through an escaping junction must be denied"
    assert "escapes workspace" in result.action_result.error
    assert not (tmp_path / "secret" / "key.txt").read_text(encoding="utf-8").startswith("X")


def test_unknown_action_raises(registry: ActionRegistry) -> None:
    engine = _executor(registry)
    with pytest.raises(NotFoundError):
        _run(engine, "ghost.action", {})


def test_missing_authorization_denied(registry: ActionRegistry) -> None:
    engine = ExecutionEngine(registry=registry, guardrails=GuardrailService(
        capabilities=CapabilityRegistry(), policies=PolicyEngine()
    ))
    result = _run(engine, "filesystem.write", {"path": "f.txt", "content": "x"})
    assert not result.ok
    assert "not granted" in result.action_result.error


def test_approval_required_for_high_risk_cleanup(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    denied = _run(engine, "workspace.cleanup", {"name": "default"})
    assert not denied.ok
    assert "review" in denied.action_result.error.lower() or "approval" in denied.action_result.error.lower()
    # approving the risky operation lets it proceed
    allowed = _run(engine, "workspace.cleanup", {"name": "default"}, approval=True)
    assert allowed.ok and allowed.action_result.output["removed"] == "default"


def test_disallowed_command_rejected(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    # Approval is given so the gate passes and the allowlist check must reject.
    result = _approved(engine, "process.run", {"command": "powershell", "args": ["/C", "del *"]})
    assert not result.ok
    assert "not allowlisted" in result.action_result.error


def test_process_timeout_enforced(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    result = _approved(
        engine,
        "process.run",
        {"command": sys.executable, "args": ["-c", "import time; time.sleep(5)"], "timeout_seconds": 0.8},
    )
    assert not result.ok
    assert "exceeded 0.8s" in result.action_result.error


def test_cancellation_prevents_work(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    token = CancellationToken()
    token.cancel()
    result = _run(
        engine,
        "process.run",
        {"command": sys.executable, "args": ["-c", "pass"]},
        approval=True,
        cancellation=token,
    )
    assert not result.ok
    assert "cancelled" in result.action_result.error.lower()


def test_output_size_limit_truncates_with_flag(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    result = _approved(
        engine,
        "process.run",
        {"command": sys.executable, "args": ["-c", "print('x' * 200000)"]},
    )
    assert result.ok
    output = result.action_result.output
    assert output["stdout_truncated"] is True
    assert len(output["stdout"]) == manager._max_output_bytes  # noqa: SLF001
    assert len(output["stdout"]) <= MAX_OUTPUT_BYTES_DEFAULT


def test_execution_metadata_present(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    result = _approved(engine, "process.run", {"command": sys.executable, "args": ["-c", "print('m')"]})
    assert result.ok
    meta = result.action_result.output
    assert meta["exit_code"] == 0
    assert "command" in meta and "duration_ms" in meta
    assert "args" in meta and isinstance(meta["args"], list)


def test_audit_events_for_success_and_failure(manager: WorkspaceManager, registry: ActionRegistry) -> None:
    engine = _executor(registry)
    _run(engine, "filesystem.write", {"path": "ok.txt", "content": "hello"})
    _run(engine, "filesystem.write", {"path": "../../evil.txt", "content": "x"})
    actions = [e.action for e in manager._audit.entries()]  # noqa: SLF001
    assert "workspace.write" in actions
    denied = [e for e in manager._audit.entries() if e.decision == "deny"]
    assert any("escapes workspace" in e.reason for e in denied)


def test_invalid_workspace_name_rejected(manager: WorkspaceManager) -> None:
    with pytest.raises(WorkspaceError):
        manager.create_workspace("../nope")
    with pytest.raises(WorkspaceError):
        manager.create_workspace("a/b")  # slash is not allowed in a name


def test_cleanup_refuses_unowned_directory(manager: WorkspaceManager) -> None:
    # simulate an attacker planting a directory at the managed root
    planted = manager.root / "planted"
    planted.mkdir()
    with pytest.raises(WorkspaceError):
        manager.cleanup("planted")