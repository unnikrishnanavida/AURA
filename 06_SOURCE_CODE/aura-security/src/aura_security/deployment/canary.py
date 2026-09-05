"""Canary deployment.

A canary applies an approved remediation to a small, isolated subset first and
requires a health signal before promoting to full activation. If the canary
fails, nothing is promoted and the change can be rolled back.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aura_security.models.remediation_plan import Remediation


@dataclass(frozen=True, slots=True)
class CanaryResult:
    canary_id: str
    remediation_id: str
    promoted: bool
    health_score: float
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "canary_id": self.canary_id,
            "remediation_id": self.remediation_id,
            "promoted": self.promoted,
            "health_score": self.health_score,
            "reason": self.reason,
        }


class CanaryDeployer:
    """Applies remediations to a canary subset and promotes on health.

    The apply/promote callbacks are provided by the deployment environment;
    the deployer itself never writes to production.
    """

    def __init__(self, *, min_health_score: float = 0.8) -> None:
        if not 0.0 <= min_health_score <= 1.0:
            raise ValueError("min_health_score must be in [0,1]")
        self._min_health_score = min_health_score
        self._results: list[CanaryResult] = []

    def run(
        self,
        remediation: Remediation,
        *,
        apply_canary: Callable[[Remediation], float],
        promote: Callable[[Remediation], None],
        canary_id: str | None = None,
    ) -> CanaryResult:
        identifier = canary_id or f"canary-{remediation.id}"
        try:
            health_score = apply_canary(remediation)
        except (RuntimeError, ValueError, OSError) as exc:  # a canary failure must not reach production
            result = CanaryResult(
                canary_id=identifier,
                remediation_id=remediation.id,
                promoted=False,
                health_score=0.0,
                reason=str(exc),
            )
            self._results.append(result)
            return result

        if health_score >= self._min_health_score:
            promote(remediation)
            result = CanaryResult(
                canary_id=identifier,
                remediation_id=remediation.id,
                promoted=True,
                health_score=health_score,
            )
        else:
            result = CanaryResult(
                canary_id=identifier,
                remediation_id=remediation.id,
                promoted=False,
                health_score=health_score,
                reason=f"health {health_score:.2f} below threshold {self._min_health_score:.2f}",
            )
        self._results.append(result)
        return result

    def history(self) -> list[CanaryResult]:
        return list(self._results)


__all__ = ["CanaryDeployer", "CanaryResult"]
