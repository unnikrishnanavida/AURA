"""Health and readiness checks for aura-api.

Health = liveness (process is up). Readiness = whether the service can serve
traffic (dependencies available). Both return structured, truthful results.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

HealthCheck = Callable[[], tuple[bool, str]]


@dataclass
class HealthRegistry:
    """A registry of named health/readiness checks."""

    checks: dict[str, HealthCheck] = field(default_factory=dict)

    def register(self, name: str, check: HealthCheck) -> None:
        self.checks[name] = check

    def run(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for name, check in self.checks.items():
            try:
                ok_flag, detail = check()
            except Exception as exc:  # noqa: BLE001 - a failing check must not crash health
                ok_flag, detail = False, f"check raised: {type(exc).__name__}"
            results.append({"name": name, "ok": ok_flag, "detail": detail})
        return results


def liveness() -> dict[str, object]:
    """A process that runs this function is alive."""
    return {"status": "ok", "service": "aura-api"}


def readiness(registry: HealthRegistry) -> dict[str, object]:
    """True readiness requires every registered dependency check to pass."""
    results = registry.run()
    ready = all(r["ok"] for r in results)
    return {
        "status": "ready" if ready else "not_ready",
        "checks": results,
    }


__all__ = ["HealthRegistry", "liveness", "readiness"]