"""Command implementations for aura-cli.

Each command performs real work and returns a :class:`CommandResult` with a
stable exit code. No command prints "Success" without doing something real.
"""

from __future__ import annotations

from typing import Any

from aura_cli.config.profiles import ProfileLoader
from aura_cli.core.result import (
    CliError,
    CommandResult,
    ConfigInvalidError,
    ExitCode,
    NotSupportedError,
)
from aura_cli.integrations.aura.runtime import RuntimeAdapter
from aura_cli.security.gate import ConfirmationGate


def _ok(output: dict[str, Any], lines: list[str] | None = None) -> CommandResult:
    return CommandResult(exit_code=ExitCode.OK, output=output, human_lines=lines or [])


class CommandDispatcher:
    """Dispatches CLI commands to real functionality."""

    def __init__(
        self,
        runtime: RuntimeAdapter | None = None,
        profiles: ProfileLoader | None = None,
        gate: ConfirmationGate | None = None,
    ) -> None:
        self.runtime = runtime or RuntimeAdapter()
        self.profiles = profiles or ProfileLoader()
        self.gate = gate or ConfirmationGate()

    def doctor(self) -> CommandResult:
        checks = self.runtime.doctor()
        all_ok = all(c["ok"] for c in checks)
        return _ok(
            {"checks": checks, "all_ok": all_ok},
            [f"[{'ok' if c['ok'] else 'MISSING'}] {c['name']}" for c in checks],
        )

    def health(self) -> CommandResult:
        report = self.runtime.health()
        output = {
            "canonical_runtime": report.canonical,
            "health": report.health,
            "subsystems": report.subsystems,
        }
        lines = [f"canonical runtime: {'available' if report.canonical else 'UNVAILABLE'}"]
        lines.append(f"status: {report.health.get('status', 'unknown')}")
        for name, available in report.subsystems.items():
            lines.append(f"{name}: {'available' if available else 'unavailable'}")
        return _ok(output, lines)

    def config_validate(self, profile: str = "default") -> CommandResult:
        try:
            loaded = self.profiles.load(profile)
        except ConfigInvalidError as exc:
            return CommandResult(
                exit_code=ExitCode.CONFIG_INVALID,
                output={"valid": False, "error": exc.message, "profile": profile},
                error=exc,
            )
        return _ok(
            {"valid": True, "profile": loaded.to_dict()},
            [f"profile {loaded.name!r} is valid", f"  runtime={loaded.runtime}", f"  output={loaded.output}"],
        )

    def version(self, version: str) -> CommandResult:
        return _ok({"version": version}, [version])

    def run(self, question: str) -> CommandResult:
        try:
            result = self.runtime.reasoning(question)
        except NotSupportedError as exc:
            return CommandResult(exit_code=ExitCode.NOT_SUPPORTED, output={"supported": False}, error=exc)
        return _ok(result, [result.get("outcome", "ran")])

    def knowledge(self) -> CommandResult:
        try:
            summary = self.runtime.knowledge_summary()
        except NotSupportedError as exc:
            return CommandResult(exit_code=ExitCode.NOT_SUPPORTED, output={"supported": False}, error=exc)
        return _ok(summary, [f"claims in engine: {summary['claims']}"])

    def security_audit(self, *, confirmed: bool) -> CommandResult:
        """Dangerous operation: MUST be confirmed."""
        self.gate.confirmed = set()
        if confirmed:
            self.gate.confirmed.add("security_audit")
        try:
            self.gate.confirm("security_audit")
        except CliError as exc:
            return CommandResult(exit_code=ExitCode.DENIED, output={"confirmed": False}, error=exc)
        # Real audit data from the canonical runtime when available
        try:
            from aura.security.audit import audit_log

            entries = audit_log().entries()[-20:]
            audit = [e.to_dict() for e in entries]
            return _ok({"audit_entries": len(audit), "entries": audit})
        except Exception:  # noqa: BLE001 - canonical audit may be unavailable
            return _ok({"audit_entries": 0, "entries": [], "note": "canonical audit log not available"})

    def plan(self, goal: str) -> CommandResult:
        """Real planning via the canonical planning engine when available."""
        try:
            from aura.planning.engine import PlanningEngine
            from aura.planning.models import Goal, Task
        except Exception as exc:  # noqa: BLE001
            return CommandResult(
                exit_code=ExitCode.NOT_SUPPORTED,
                output={"supported": False, "reason": str(exc)},
                error=NotSupportedError(str(exc)),
            )
        from aura.foundation.ids import GoalId

        g = Goal(id=GoalId.new(), description=goal)
        tasks = [
            Task(name="analyze", capability="domain.analyze"),
            Task(name="execute", capability="domain.execute"),
        ]
        result = PlanningEngine().plan(goal=g, tasks=tasks)
        primary = result.primary
        if primary is None:
            return _ok(
                {
                    "goal": goal,
                    "valid": False,
                    "issues": list(result.issues),
                    "alternatives": len(result.alternatives),
                },
                [f"no valid plan for {goal!r}", *[f"  issue: {i}" for i in result.issues]],
            )
        return _ok(
            {
                "goal": goal,
                "valid": result.validation.valid if result.validation else True,
                "steps": [s.task.name for s in primary.steps],
                "risk": primary.risk.risk_score if hasattr(primary.risk, "risk_score") else str(primary.risk),
                "alternatives": len(result.alternatives),
            },
            [f"created plan for {goal!r}", f"  steps: {', '.join(s.task.name for s in primary.steps)}"],
        )


__all__ = ["CommandDispatcher"]