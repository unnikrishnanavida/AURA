"""Threat assessment models for AURA Adaptive Defense.

A Threat is an observed security event. An Assessment adds classification,
evidence, severity, and confidence so downstream stages can decide whether
remediation is warranted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ThreatSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackClass(str, Enum):
    INJECTION = "injection"
    PATH_TRAVERSAL = "path_traversal"
    AUTH_BYPASS = "auth_bypass"
    PERMISSION_ESCALATION = "permission_escalation"
    SECRET_EXPOSURE = "secret_exposure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SUPPLY_CHAIN = "supply_chain"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Threat:
    """One observed security event with its raw indicators."""

    id: str
    kind: str
    indicators: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "indicators": self.indicators,
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ThreatAssessment:
    """Evaluated threat: classified, scored, and evidenced."""

    threat: Threat
    attack_class: AttackClass
    severity: ThreatSeverity
    confidence: float  # 0..1
    evidence: tuple[str, ...] = ()
    root_cause_hint: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0,1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat_id": self.threat.id,
            "class": self.attack_class.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }


class ThreatClassifier:
    """Deterministic classification of a threat from indicator patterns."""

    _RULES: tuple[tuple[str, AttackClass], ...] = (
        ("sql", AttackClass.INJECTION),
        ("command", AttackClass.INJECTION),
        ("traversal", AttackClass.PATH_TRAVERSAL),
        ("../", AttackClass.PATH_TRAVERSAL),
        ("bypass", AttackClass.AUTH_BYPASS),
        ("escalation", AttackClass.PERMISSION_ESCALATION),
        ("secret", AttackClass.SECRET_EXPOSURE),
        ("key", AttackClass.SECRET_EXPOSURE),
        ("token", AttackClass.SECRET_EXPOSURE),
        ("exhaustion", AttackClass.RESOURCE_EXHAUSTION),
        ("rate", AttackClass.RESOURCE_EXHAUSTION),
        ("dependency", AttackClass.SUPPLY_CHAIN),
        ("package", AttackClass.SUPPLY_CHAIN),
    )

    def classify(self, threat: Threat) -> ThreatAssessment:
        haystack = f"{threat.kind} {threat.indicators}".lower()
        matched: AttackClass | None = None
        evidence: list[str] = []
        for token, attack_class in self._RULES:
            if token.lower() in haystack:
                matched = attack_class
                evidence.append(token)
        if matched is None:
            matched = AttackClass.UNKNOWN
            evidence = ["no classifier matched"]

        severity = self._severity(matched, threat.indicators.get("severity"))
        confidence = self._confidence(len(evidence), sparse=matched is AttackClass.UNKNOWN)
        return ThreatAssessment(
            threat=threat,
            attack_class=matched,
            severity=severity,
            confidence=confidence,
            evidence=tuple(evidence),
        )

    @staticmethod
    def _severity(attack_class: AttackClass, explicit: Any) -> ThreatSeverity:
        if explicit is not None:
            try:
                return ThreatSeverity(str(explicit).lower())
            except ValueError:
                pass
        base = {
            AttackClass.SECRET_EXPOSURE: ThreatSeverity.HIGH,
            AttackClass.PERMISSION_ESCALATION: ThreatSeverity.HIGH,
            AttackClass.AUTH_BYPASS: ThreatSeverity.HIGH,
            AttackClass.PATH_TRAVERSAL: ThreatSeverity.MEDIUM,
            AttackClass.INJECTION: ThreatSeverity.MEDIUM,
            AttackClass.RESOURCE_EXHAUSTION: ThreatSeverity.MEDIUM,
            AttackClass.SUPPLY_CHAIN: ThreatSeverity.MEDIUM,
            AttackClass.UNKNOWN: ThreatSeverity.LOW,
        }
        return base[attack_class]

    @staticmethod
    def _confidence(evidence_count: int, *, sparse: bool) -> float:
        if sparse:
            return 0.3
        return min(0.95, 0.4 + 0.3 * evidence_count)


__all__ = ["AttackClass", "Threat", "ThreatAssessment", "ThreatClassifier", "ThreatSeverity"]
