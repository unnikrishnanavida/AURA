"""Tests for aura-cli main() dispatch: exit codes, JSON output, non-interactive mode."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_cli.__main__ import main


def test_version_exit_zero():
    assert main(["version"]) == 0


def test_unknown_command_prints_help_and_returns_usage_error():
    assert main(["frobnicate"]) == 2  # argparse usage-error exit code (stable)


def test_health_json_output_is_parseable():
    out = io.StringIO()
    with redirect_stdout(out):
        rc = main(["--output", "json", "health"])
    assert rc == 0
    payload = json.loads(out.getvalue())
    assert payload["ok"] is True
    assert "data" in payload


def test_run_question_returns_zero():
    assert main(["run", "what", "is", "two", "plus", "two"]) == 0


def test_config_validate_invalid_profile_exit_2():
    assert main(["config", "validate"]) == 0  # default profile exists
    out = io.StringIO()
    with redirect_stderr(out), redirect_stdout(io.StringIO()):
        rc = main(["--profile", "missing-profile", "config", "validate"])
    assert rc == 2


def test_dangerous_operation_fails_closed_non_interactive():
    out = io.StringIO()
    with redirect_stderr(out), redirect_stdout(io.StringIO()):
        rc = main(["--non-interactive", "security", "audit"])
    assert rc == 4  # DENIED


def test_dangerous_operation_confirmed_runs():
    assert main(["--non-interactive", "security", "audit", "--yes"]) == 0


def test_plan_command_exit_stable():
    rc = main(["plan", "research", "biology"])
    assert rc in (0, 5)