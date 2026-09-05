"""Tests for aura-cli commands (real behavior, stable exit codes)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_cli import __version__
from aura_cli.app.commands import CommandDispatcher
from aura_cli.core.result import ExitCode
from aura_cli.security.gate import ConfirmationGate


@pytest.fixture
def dispatcher() -> CommandDispatcher:
    return CommandDispatcher()


def test_doctor_returns_zero_when_all_ok():
    result = CommandDispatcher().doctor()
    assert result.exit_code == ExitCode.OK
    assert result.output["all_ok"] is True
    assert result.output["checks"]


def test_health_canonical_available():
    result = CommandDispatcher().health()
    assert result.exit_code == ExitCode.OK
    assert "canonical_runtime" in result.output
    assert "subsystems" in result.output


def test_config_validate_default_profile():
    result = CommandDispatcher().config_validate("default")
    assert result.exit_code == ExitCode.OK
    assert result.output["valid"] is True
    assert result.output["profile"]["name"] == "default"


def test_config_validate_missing_profile_returns_config_invalid():
    result = CommandDispatcher().config_validate("does-not-exist")
    assert result.exit_code == ExitCode.CONFIG_INVALID
    assert result.output["valid"] is False


def test_version_command():
    result = CommandDispatcher().version(__version__)
    assert result.exit_code == ExitCode.OK
    assert result.output["version"] == __version__


def test_knowledge_command_runs_real_engine():
    result = CommandDispatcher().knowledge()
    assert result.exit_code == ExitCode.OK
    assert result.output["claims"] >= 1


def test_security_audit_fails_closed_in_non_interactive_mode():
    gate = ConfirmationGate(non_interactive=True)
    dispatcher = CommandDispatcher(gate=gate)
    result = dispatcher.security_audit(confirmed=False)
    assert result.exit_code == ExitCode.DENIED
    assert result.error is not None


def test_security_audit_confirmed_runs():
    gate = ConfirmationGate(non_interactive=True)
    dispatcher = CommandDispatcher(gate=gate)
    result = dispatcher.security_audit(confirmed=True)
    assert result.exit_code == ExitCode.OK
    assert "audit_entries" in result.output


def test_result_to_dict_shape():
    result = CommandDispatcher().config_validate("default")
    payload = result.to_dict()
    assert payload["exit_code"] == ExitCode.OK
    assert payload["ok"] is True
    assert payload["error"] is None


def test_plan_command_calls_canonical_engine():
    result = CommandDispatcher().plan("research quantum computing")
    # Either the canonical engine produced a real plan, or it is explicitly
    # unsupported in this environment. Both are honest outcomes.
    assert result.exit_code in (ExitCode.OK, ExitCode.NOT_SUPPORTED)
    if result.exit_code == ExitCode.OK:
        assert "steps" in result.output