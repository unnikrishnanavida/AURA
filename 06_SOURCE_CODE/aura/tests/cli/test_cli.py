"""CLI tests: parser surface, real readiness, real security posture (CLI-1)."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from aura.cli.main import _Cmd, build_parser


def test_parser_exposes_all_commands() -> None:
    from argparse import _SubParsersAction

    parser = build_parser()
    sub = next(
        (a for a in parser._actions if isinstance(a, _SubParsersAction)), None  # noqa: SLF001
    )
    assert sub is not None
    assert {"doctor", "health", "ready", "config", "run", "replay", "security", "audit", "version"} <= set(
        sub.choices
    )


def test_ready_reports_real_store_probe() -> None:
    cmd = _Cmd()
    out = io.StringIO()
    with redirect_stdout(out):
        code = cmd.ready()
    payload = json.loads(out.getvalue())
    assert code == 0
    assert payload["status"] in {"ready", "not_ready"}
    assert "store_entries" in payload  # a real store probe ran


def test_security_status_reports_real_runtime_state() -> None:
    cmd = _Cmd()
    out = io.StringIO()
    with redirect_stdout(out):
        code = cmd.security_status()
    text = out.getvalue()
    assert code == 0
    assert "real runtime state" in text
    assert "engine health" in text
    assert "provider:" in text