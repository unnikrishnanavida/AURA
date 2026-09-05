"""Health and readiness contract primitives for aura-core."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

HealthCheck = Callable[[], tuple[bool, str]]


@dataclass
class HealthRegistry:
    """Named health/readiness checks with instance-scoped state."""

    checks: dict[str, HealthCheck] = field(default_factory=dict)

    def register(self, name: str, check: HealthCheck) -> None:
        self.checks[name] = check

    def run(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for name, check in self.checks.items():
            try:
                ok_flag, detail = check()
            except Exception as exc:  # noqa: BLE001 - a failing check must not crash health
                ok_flag, detail = False, f"check raised: {type(exc).__name__}"
            results.append({"name": name, "ok": ok_flag, "detail": detail})
        return results

    def healthy(self) -> bool:
        return all(r["ok"] for r in self.run())


@dataclass(frozen=True)
class HealthSummary:
    """A structured health snapshot."""

    ok: bool
    checks: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": list(self.checks)}


@dataclass(frozen=True)
class ReadinessSummary:
    """A structured readiness snapshot."""

    ready: bool
    checks: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "checks": list(self.checks)}


__all__ = ["HealthCheck", "HealthRegistry", "HealthSummary", "ReadinessSummary"]