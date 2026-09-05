"""Diagnostics for aura-desktop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Check = Callable[[], tuple[bool, str]]


@dataclass
class DiagnosticReport:
    """A structured diagnostics result."""

    checks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(c["ok"] for c in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {"all_ok": self.all_ok, "checks": list(self.checks)}


class DiagnosticsRunner:
    """Runs named diagnostic checks and produces a report."""

    def __init__(self) -> None:
        self._checks: dict[str, Check] = {}

    def register(self, name: str, check: Check) -> None:
        self._checks[name] = check

    def run(self) -> DiagnosticReport:
        report = DiagnosticReport()
        for name, check in self._checks.items():
            try:
                ok_flag, detail = check()
            except Exception as exc:  # noqa: BLE001 - diagnostics never crash
                ok_flag, detail = False, f"check raised: {type(exc).__name__}"
            report.checks.append({"name": name, "ok": ok_flag, "detail": detail})
        return report


__all__ = ["DiagnosticReport", "DiagnosticsRunner"]