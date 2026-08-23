"""Process sandbox: the execution boundary for effectful tools.

The sandbox runs a tool's command in a fresh subprocess with:

- a hard wall-clock timeout (the process is terminated by ``subprocess``),
- captured stdout/stderr and exit status,
- a guard against a small set of catastrophic command fragments.

No tool reaches the host shell directly; ``shell=True`` is never used, and
``argv`` is always passed as an explicit list.
"""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.errors import ToolExecutionError

__all__ = [
    "SandboxRequest",
    "SandboxResult",
    "ProcessSandbox",
    "is_subpath",
]

#: Command fragments that are refused before execution regardless of policy.
FORBIDDEN_FRAGMENTS: tuple[str, ...] = (
    "rm -rf /",
    "--no-preserve-root",
    "> /dev/sda",
    "mkfs.",
    ":(){ :|:& };:",
)


def is_subpath(candidate: str, root: str) -> bool:
    """True when ``candidate`` resolves inside ``root`` (path-traversal guard)."""
    import os

    candidate_abs = os.path.abspath(candidate)
    root_abs = os.path.abspath(root)
    try:
        common = os.path.commonpath([root_abs, candidate_abs])
    except ValueError:
        return False
    return common == root_abs


@dataclass(frozen=True)
class SandboxRequest:
    """A request to execute a command inside a sandbox."""

    argv: list[str]
    cwd: str | None = None
    timeout_s: float = 30.0
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SandboxResult:
    """Outcome of a sandboxed execution.

    Timeouts are *reported* (``timed_out=True``), never raised, so the
    execution engine can classify the failure and apply recovery.
    """

    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class ProcessSandbox:
    """Runs commands in isolated subprocesses with capture and timeouts."""

    def __init__(self, forbidden_fragments: tuple[str, ...] = FORBIDDEN_FRAGMENTS) -> None:
        self._forbidden = forbidden_fragments

    def execute(self, request: SandboxRequest) -> SandboxResult:
        if not request.argv:
            raise ToolExecutionError("sandbox refused: empty command")
        joined = shlex.join(request.argv)
        for fragment in self._forbidden:
            if fragment.lower() in joined.lower():
                raise ToolExecutionError(
                    f"sandbox refused dangerous command fragment {fragment!r}"
                )
        started = time.monotonic()
        timed_out = False
        stdout = ""
        stderr = ""
        exit_code = -1
        try:
            proc = subprocess.run(
                request.argv,
                cwd=request.cwd,
                env=request.env or None,
                capture_output=True,
                text=True,
                timeout=request.timeout_s,
                check=False,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            if exc.stdout:
                stdout = exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode(errors="replace")
            if exc.stderr:
                stderr = exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode(errors="replace")
        duration = time.monotonic() - started
        return SandboxResult(
            argv=tuple(request.argv),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_s=duration,
            timed_out=timed_out,
        )