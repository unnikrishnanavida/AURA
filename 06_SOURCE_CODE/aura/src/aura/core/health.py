"""Health and readiness.

Components return a :class:`HealthReport`; the aggregator combines them into a
single readiness decision. Liveness vs readiness are distinct: liveness shows
the process is alive; readiness shows it can accept work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from aura.foundation.clock import Clock, SystemClock


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ReadinessStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class HealthReport:
    component: str
    status: HealthStatus
    detail: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime | None = None

    @property
    def ok(self) -> bool:
        return self.status is HealthStatus.OK


@runtime_checkable
class HealthCheckable(Protocol):
    def health(self) -> HealthReport: ...


class HealthAggregator:
    """Combines component health reports into overall readiness."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._checks: dict[str, HealthCheckable] = {}

    def register(self, component: str, checker: HealthCheckable) -> None:
        if component in self._checks:
            raise ValueError(f"health component already registered: {component}")
        self._checks[component] = checker

    def unregister(self, component: str) -> None:
        self._checks.pop(component, None)

    def reports(self) -> list[HealthReport]:
        now = self._clock.now()
        reports: list[HealthReport] = []
        for name, checker in sorted(self._checks.items()):
            try:
                report = checker.health()
                reports.append(
                    HealthReport(
                        component=name,
                        status=report.status,
                        detail=report.detail,
                        checked_at=now,
                    )
                )
            except Exception as exc:
                reports.append(
                    HealthReport(
                        component=name,
                        status=HealthStatus.UNHEALTHY,
                        detail={"error": str(exc)},
                        checked_at=now,
                    )
                )
        return reports

    def readiness(self) -> Readiness:
        reports = self.reports()
        if not reports:
            return Readiness(status=ReadinessStatus.READY, reports=[])
        if any(r.status is HealthStatus.UNHEALTHY for r in reports):
            worst = HealthStatus.UNHEALTHY
        elif any(r.status is HealthStatus.DEGRADED for r in reports):
            worst = HealthStatus.DEGRADED
        else:
            worst = HealthStatus.OK
        status = ReadinessStatus.READY if worst is HealthStatus.OK else ReadinessStatus.NOT_READY
        return Readiness(status=status, reports=reports, worst=worst)


@dataclass(frozen=True)
class Readiness:
    status: ReadinessStatus
    reports: list[HealthReport]
    worst: HealthStatus = HealthStatus.OK


__all__ = ["HealthAggregator", "HealthReport", "HealthStatus", "Readiness", "ReadinessStatus"]