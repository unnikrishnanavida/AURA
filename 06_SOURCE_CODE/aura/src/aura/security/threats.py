"""Threat detection.

Concrete, explainable detectors (no AI-powered hand-waving) that turn real
signals into actionable :class:`Incident` records:

- brute-force authentication (N failures from one source in a window);
- rate-limit abuse (denials crossing a threshold in a window);
- privilege violations (repeated authorization denials from one source).

Detectors are fed by the existing metric/audit streams and are deterministic
and testable. ``ThreatMonitor`` composes detectors + the incident manager.
"""

from __future__ import annotations

import time
from collections import deque

from aura.security.incident import Incident, IncidentManager, IncidentSeverity


class ThreatDetector:
    """Base class: feed a typed signal; get incidents back."""

    name = "detector"
    severity = IncidentSeverity.MEDIUM

    def __init__(self, *, window_seconds: float = 300.0, threshold: int = 10) -> None:
        self.window_seconds = window_seconds
        self.threshold = threshold
        self._events: dict[str, deque[float]] = {}

    def feed(self, *, key: str) -> bool:
        """Record one event for ``key``; True when the threshold is crossed."""
        now = time.monotonic()
        bucket = self._events.setdefault(key, deque())
        while bucket and bucket[0] < now - self.window_seconds:
            bucket.popleft()
        bucket.append(now)
        return len(bucket) >= self.threshold

    def counts(self) -> dict[str, int]:
        now = time.monotonic()
        out: dict[str, int] = {}
        for key, bucket in self._events.items():
            out[key] = sum(1 for ts in bucket if ts >= now - self.window_seconds)
        return out

    def reset(self) -> None:
        self._events.clear()


class BruteForceDetector(ThreatDetector):
    name = "brute_force"
    severity = IncidentSeverity.HIGH

    def __init__(self, *, threshold: int = 10, window_seconds: float = 300.0) -> None:
        super().__init__(window_seconds=window_seconds, threshold=threshold)

    def analyze(self, *, ip: str) -> bool:
        return self.feed(key=ip)


class RateAbuseDetector(ThreatDetector):
    name = "rate_abuse"
    severity = IncidentSeverity.MEDIUM

    def __init__(self, *, threshold: int = 50, window_seconds: float = 300.0) -> None:
        super().__init__(window_seconds=window_seconds, threshold=threshold)

    def analyze(self, *, ip: str) -> bool:
        return self.feed(key=ip)


class PrivilegeViolationDetector(ThreatDetector):
    name = "privilege_violation"
    severity = IncidentSeverity.HIGH

    def __init__(self, *, threshold: int = 5, window_seconds: float = 600.0) -> None:
        super().__init__(window_seconds=window_seconds, threshold=threshold)

    def analyze(self, *, actor: str) -> bool:
        return self.feed(key=actor)


class ThreatMonitor:
    """Composes detectors and opens (or refreshes) incidents on threshold crosses."""

    def __init__(self, manager: IncidentManager, detectors: list[ThreatDetector] | None = None) -> None:
        self._manager = manager
        self._detectors: dict[str, ThreatDetector] = {}
        for detector in detectors or ():
            self.register(detector)

    def register(self, detector: ThreatDetector) -> None:
        self._detectors[detector.name] = detector

    def detectors(self) -> list[str]:
        return sorted(self._detectors)

    def assess(
        self,
        *,
        auth_failures: dict[str, int] | None = None,
        rate_denials: dict[str, int] | None = None,
        authz_denials: dict[str, int] | None = None,
    ) -> list[Incident]:
        """Evaluate signal counters (ip/actor -> count) and update incidents."""
        opened: list[Incident] = []
        for ip, count in (auth_failures or {}).items():
            detector = self._detectors.get("brute_force")
            if detector is not None and count >= detector.threshold:
                opened.append(
                    self._manager.open(
                        title="brute-force authentication attempt",
                        severity=detector.severity,
                        source=detector.name,
                        evidence={"ip": ip, "failures_in_window": count},
                    )
                )
        for ip, count in (rate_denials or {}).items():
            detector = self._detectors.get("rate_abuse")
            if detector is not None and count >= detector.threshold:
                opened.append(
                    self._manager.open(
                        title="rate-limit abuse",
                        severity=detector.severity,
                        source=detector.name,
                        evidence={"ip": ip, "denials_in_window": count},
                    )
                )
        for actor, count in (authz_denials or {}).items():
            detector = self._detectors.get("privilege_violation")
            if detector is not None and count >= detector.threshold:
                opened.append(
                    self._manager.open(
                        title="authorization violations",
                        severity=detector.severity,
                        source=detector.name,
                        evidence={"actor": actor, "denials_in_window": count},
                    )
                )
        return opened


__all__ = [
    "BruteForceDetector",
    "PrivilegeViolationDetector",
    "RateAbuseDetector",
    "ThreatDetector",
    "ThreatMonitor",
]