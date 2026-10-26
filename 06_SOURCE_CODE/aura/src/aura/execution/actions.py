"""Secure workspace, filesystem, and process action family (SRC-1).

Opt-in, guardrail-gated actions for confined software work, built on the
canonical :class:`~aura.execution.registry.ActionRegistry` and
:class:`~aura.execution.models.ActionSpec` contracts. Nothing is registered by
default: an operator wires :func:`WorkspaceManager.install` into the action
registry their runtime owns, and every action still passes the normal
guardrail gate (capability -> permission -> safety -> autonomy -> budget) at
the authoritative execution boundary.

Guarantees enforced *here* (and only these are claimed):

* workspace-root confinement — normalized containment check with symlink /
  junction resolution and ``..`` traversal rejection;
* default-deny — only the explicitly implemented action names exist;
* allowlisted process execution with ``shell=False``, a bounded timeout, and a
  hard output-size cap with explicit truncation flags;
* read/write size caps for file content;
* cooperative cancellation (checked before work starts; running processes are
  terminated on cancellation or timeout);
* structured audit — every executed or rejected operation is recorded through
  the injected audit sink;
* cleanup restricted to workspaces this manager created.

This module does NOT provide: arbitrary shell execution, unrestricted
filesystem access, credential access, dependency installation, global
environment mutation, deployment, or network access.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from aura.execution.models import ActionInputs, ActionResult, ActionSpec, make_result
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.foundation.errors import AuraError

_PROCESS_ALLOWLIST_DEFAULT: tuple[str, ...] = ("python", "python3", "pytest", "node")
MAX_OUTPUT_BYTES_DEFAULT = 65_536  # 64 KiB
MAX_FILE_BYTES_DEFAULT = 1_048_576  # 1 MiB
DEFAULT_TIMEOUT_SECONDS = 15.0
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class WorkspaceError(AuraError):
    """Raised for any workspace/path violation (escape, invalid name, unknown)."""

    code = "workspace.violation"


def _sanitize_name(name: str) -> str:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise WorkspaceError(f"invalid workspace name: {name!r}")
    return name


def _within(root: Path, candidate: Path) -> bool:
    root_norm = os.path.normcase(str(root))
    candidate_norm = os.path.normcase(str(candidate))
    return candidate_norm == root_norm or candidate_norm.startswith(root_norm + os.sep)


def _clip(text: str, limit: int) -> tuple[str, bool]:
    """Truncate to ``limit`` characters (bytes proxied as chars) with a flag."""
    if len(text) <= limit:
        return text, False
    return text[:limit], True


class Workspace:
    """One confined directory the manager created or manages."""

    def __init__(self, root: Path, *, create: bool = False) -> None:
        self.root = Path(root).resolve()
        if create:
            self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise WorkspaceError(f"workspace root is not a directory: {self.root}")

    def resolve(self, rel: str | Path) -> Path:
        """Resolve a user-supplied path to a real path guaranteed inside root.

        ``Path.resolve()`` follows symlinks and junctions, so a link planted
        inside the workspace cannot escape the root: the resolved candidate
        is checked for containment after normalization.
        """
        if rel is None:
            raise WorkspaceError("path is required")
        raw = rel if isinstance(rel, Path) else Path(str(rel).strip() or ".")
        if raw.is_absolute():
            # Absolute paths are allowed only when they resolve inside root.
            pass
        candidate = (self.root / raw).resolve()
        if not _within(self.root, candidate):
            raise WorkspaceError(f"path escapes workspace root: {rel!r}")
        return candidate

    def ensure_dir(self, rel: str | Path) -> Path:
        path = self.resolve(rel)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def relative(self, path: Path) -> str:
        return os.path.relpath(path, self.root)


class WorkspaceManager:
    """Owns a set of confined workspaces and installs the action family.

    One manager may own many workspaces beneath a single ``workspaces_root``.
    ``cleanup`` is refused for any workspace this manager did not create — a
    second layer of confinement on top of the path check.
    """

    def __init__(
        self,
        *,
        workspaces_root: str | Path,
        audit: Any = None,
        allowlist: tuple[str, ...] = _PROCESS_ALLOWLIST_DEFAULT,
        max_output_bytes: int = MAX_OUTPUT_BYTES_DEFAULT,
        max_file_bytes: int = MAX_FILE_BYTES_DEFAULT,
        default_timeout: float = DEFAULT_TIMEOUT_SECONDS,
        default_workspace: str = "default",
    ) -> None:
        if max_output_bytes < 1 or max_file_bytes < 1:
            raise WorkspaceError("size caps must be positive")
        if default_timeout <= 0:
            raise WorkspaceError("default_timeout must be positive")
        self.root = Path(workspaces_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._audit = audit
        self._allowlist = set(str(c).lower() for c in allowlist)
        # The interpreter running this process is always allowed so tests and
        # operators can run the active python deterministically.
        self._allowlist.update({Path(sys.executable).name.lower(), Path(sys.executable).stem.lower()})
        self._max_output_bytes = max_output_bytes
        self._max_file_bytes = max_file_bytes
        self._default_timeout = default_timeout
        self._default_name = _sanitize_name(default_workspace)
        self._owns: set[str] = set()
        # The default workspace is created eagerly so installed actions have a
        # deterministic target and the manager provably owns it for cleanup.
        self.create_workspace(self._default_name)

    # -- lifecycle ---------------------------------------------------------
    def create_workspace(self, name: str) -> Workspace:
        safe = _sanitize_name(name)
        ws = Workspace(self.root / safe, create=True)
        self._owns.add(self._key(ws.root))
        return ws

    def open_workspace(self, name: str) -> Workspace:
        safe = _sanitize_name(name)
        return Workspace(self.root / safe)

    def _workspace(self, inputs: ActionInputs) -> Workspace:
        name = inputs.get("workspace")
        if name is None:
            return self.open_workspace(self._default_name)
        return self.open_workspace(str(name))

    def cleanup(self, name: str) -> None:
        safe = _sanitize_name(name)
        ws = Workspace(self.root / safe)
        key = self._key(ws.root)
        if key not in self._owns:
            raise WorkspaceError(f"refusing to remove workspace not created here: {name!r}")
        shutil.rmtree(ws.root)
        self._owns.discard(key)

    @staticmethod
    def _key(path: Path) -> str:
        return os.path.normcase(str(path))

    # -- audit -------------------------------------------------------------
    def _audit_action(
        self, action: str, decision: str, reason: str, payload: dict[str, object] | None = None
    ) -> None:
        record = getattr(self._audit, "record", None)
        if callable(record):
            record(
                action=f"workspace.{action}",
                actor="system",
                resource=self.root.name,
                decision=decision,
                reason=reason,
                payload=payload or {},
            )

    # -- registration ------------------------------------------------------
    def install(self, registry: ActionRegistry) -> None:
        """Register the secured action family on the canonical registry."""
        registry.register(
            ActionSpec(
                name="workspace.create",
                capability="workspace.create",
                handler=self._workspace_create,
                risk=0.1,
                expected_effects=("path",),
                timeout_seconds=10.0,
            )
        )
        registry.register(
            ActionSpec(
                name="filesystem.mkdir",
                capability="filesystem.write",
                handler=self._filesystem_mkdir,
                risk=0.2,
                expected_effects=("path",),
                timeout_seconds=10.0,
            )
        )
        registry.register(
            ActionSpec(
                name="filesystem.write",
                capability="filesystem.write",
                handler=self._filesystem_write,
                risk=0.2,
                expected_effects=("path", "bytes"),
                timeout_seconds=30.0,
            )
        )
        registry.register(
            ActionSpec(
                name="filesystem.read",
                capability="filesystem.read",
                handler=self._filesystem_read,
                risk=0.1,
                expected_effects=("path", "content", "bytes", "truncated"),
                timeout_seconds=10.0,
            )
        )
        registry.register(
            ActionSpec(
                name="filesystem.list",
                capability="filesystem.read",
                handler=self._filesystem_list,
                risk=0.1,
                expected_effects=("entries",),
                timeout_seconds=10.0,
            )
        )
        registry.register(
            ActionSpec(
                name="process.run",
                capability="process.run",
                handler=self._process_run,
                risk=0.4,
                expected_effects=("command", "exit_code", "stdout", "stderr", "duration_ms"),
                timeout_seconds=self._default_timeout + 5.0,
            )
        )
        registry.register(
            ActionSpec(
                name="workspace.cleanup",
                capability="workspace.cleanup",
                handler=self._workspace_cleanup,
                risk=0.4,  # above the safety review threshold => approval required
                expected_effects=("removed",),
                timeout_seconds=30.0,
            )
        )

    # -- handlers ----------------------------------------------------------
    def _workspace_create(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        name = str(inputs.get("name") or self._default_name)
        try:
            ws = self.create_workspace(name)
        except WorkspaceError as exc:
            self._audit_action("create", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        self._audit_action("create", "allow", "workspace created", {"path": str(ws.root)})
        return make_result(ok=True, output={"path": str(ws.root)})

    def _filesystem_write(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        try:
            ws = self._workspace(inputs)
            path = ws.resolve(inputs.get("path"))
            content = inputs.get("content")
        except WorkspaceError as exc:
            self._audit_action("write", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        if not isinstance(content, str):
            self._audit_action("write", "deny", "content must be a string")
            return make_result(ok=False, error="content must be a string")
        if len(content.encode("utf-8")) > self._max_file_bytes:
            self._audit_action("write", "deny", "content exceeds the file size cap")
            return make_result(ok=False, error="content exceeds the file size cap")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")  # no newline translation
        size = len(content.encode("utf-8"))
        self._audit_action("write", "allow", "file written", {"path": ws.relative(path), "bytes": size})
        return make_result(ok=True, output={"path": ws.relative(path), "bytes": size})

    def _filesystem_read(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        try:
            ws = self._workspace(inputs)
            path = ws.resolve(inputs.get("path"))
        except WorkspaceError as exc:
            self._audit_action("read", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        if not path.is_file():
            err = WorkspaceError(f"not a file: {ws.relative(path)}")
            self._audit_action("read", "deny", str(err))
            return make_result(ok=False, error=str(err))
        try:
            raw = path.read_bytes()
        except OSError as exc:
            self._audit_action("read", "deny", f"read failed: {exc}")
            return make_result(ok=False, error=f"read failed: {exc}")
        truncated = len(raw) > self._max_output_bytes
        content = raw[: self._max_output_bytes].decode("utf-8", errors="replace")
        self._audit_action(
            "read", "allow", "file read", {"path": ws.relative(path), "bytes": len(raw), "truncated": truncated}
        )
        return make_result(
            ok=True,
            output={
                "path": ws.relative(path),
                "content": content,
                "bytes": len(raw),
                "truncated": truncated,
            },
        )

    def _filesystem_mkdir(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        try:
            ws = self._workspace(inputs)
            path = ws.resolve(inputs.get("path"))
        except WorkspaceError as exc:
            self._audit_action("mkdir", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        path.mkdir(parents=True, exist_ok=True)
        self._audit_action("mkdir", "allow", "directory created", {"path": ws.relative(path)})
        return make_result(ok=True, output={"path": ws.relative(path)})

    def _filesystem_list(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        try:
            ws = self._workspace(inputs)
            base = ws.resolve(inputs.get("path") or ".")
        except WorkspaceError as exc:
            self._audit_action("list", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        if base.is_file():
            base = base.parent
        entries: list[dict[str, object]] = []
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            try:
                entries.append(
                    {
                        "name": child.name,
                        "path": ws.relative(child.resolve()),
                        "is_dir": child.is_dir(),
                        "size": child.stat().st_size if child.is_file() else 0,
                    }
                )
            except OSError:
                continue
        self._audit_action("list", "allow", "directory listed", {"entries": len(entries)})
        return make_result(ok=True, output={"entries": entries})

    def _process_run(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        command = inputs.get("command")
        if not isinstance(command, str) or not command.strip():
            self._audit_action("process.run", "deny", "command must be a non-empty string")
            return make_result(ok=False, error="command must be a non-empty string")
        command_name = os.path.basename(str(command))
        if command_name.lower() not in self._allowlist:
            self._audit_action("process.run", "deny", f"command not allowlisted: {command_name!r}")
            return make_result(ok=False, error=f"command not allowlisted: {command_name!r}")
        args = inputs.get("args", [])
        if not isinstance(args, (list, tuple)) or not all(isinstance(a, str) for a in args):
            self._audit_action("process.run", "deny", "args must be a list of strings")
            return make_result(ok=False, error="args must be a list of strings")
        cwd_rel = inputs.get("cwd", ".")
        try:
            ws = self._workspace(inputs)
            cwd = ws.resolve(cwd_rel)
        except WorkspaceError as exc:
            self._audit_action("process.run", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        requested = float(inputs.get("timeout_seconds") or 0.0)
        timeout = min(requested, self._default_timeout) if requested > 0 else self._default_timeout
        argv = [command, *list(args)]
        started = time.monotonic()
        proc: Any = None
        out = ""
        err = ""
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(cwd),
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            # communicate() drains the pipes (a naive poll loop deadlocks the
            # child once its output exceeds the OS pipe buffer), while the
            # per-step timeout and token checks bound the run and honor
            # cooperative cancellation.
            remaining = timeout
            drained = False
            while not drained:
                if token.cancelled:
                    proc.kill()
                    proc.communicate(timeout=1.0)
                    self._audit_action("process.run", "deny", "process cancelled", {"command": command})
                    return make_result(ok=False, error=f"process.run cancelled: {command!r}")
                if remaining <= 0.0:
                    proc.kill()
                    proc.communicate(timeout=1.0)
                    self._audit_action("process.run", "deny", "process timed out", {"command": command})
                    return make_result(
                        ok=False, error=f"process.run exceeded {timeout:.1f}s: {command!r}"
                    )
                step = min(0.25, remaining)
                try:
                    out, err = proc.communicate(timeout=step)
                    drained = True
                except subprocess.TimeoutExpired:
                    remaining -= step
        except OSError as exc:
            self._audit_action("process.run", "deny", f"spawn failed: {exc}")
            return make_result(ok=False, error=f"process.run spawn failed: {exc}")
        finally:
            if proc is not None and proc.poll() is None:
                proc.kill()
        duration_ms = (time.monotonic() - started) * 1000.0
        stdout_out, stdout_trunc = _clip(out or "", self._max_output_bytes)
        stderr_out, stderr_trunc = _clip(err or "", self._max_output_bytes)
        exit_code = int(proc.returncode if proc is not None and proc.returncode is not None else 1)
        self._audit_action(
            "process.run",
            "allow",
            "process executed",
            {"command": command, "exit_code": exit_code, "duration_ms": round(duration_ms, 3)},
        )
        return make_result(
            ok=exit_code == 0,
            output={
                "command": command,
                "args": list(args),
                "exit_code": exit_code,
                "stdout": stdout_out,
                "stderr": stderr_out,
                "stdout_truncated": stdout_trunc,
                "stderr_truncated": stderr_trunc,
                "duration_ms": round(duration_ms, 3),
            },
        )

    def _workspace_cleanup(self, inputs: ActionInputs, token: CancellationToken) -> ActionResult:
        token.check()
        name = str(inputs.get("name") or self._default_name)
        try:
            self.cleanup(name)
        except WorkspaceError as exc:
            self._audit_action("cleanup", "deny", str(exc))
            return make_result(ok=False, error=str(exc))
        self._audit_action("cleanup", "allow", "workspace removed", {"name": name})
        return make_result(ok=True, output={"removed": name})


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_FILE_BYTES_DEFAULT",
    "MAX_OUTPUT_BYTES_DEFAULT",
    "Workspace",
    "WorkspaceError",
    "WorkspaceManager",
]