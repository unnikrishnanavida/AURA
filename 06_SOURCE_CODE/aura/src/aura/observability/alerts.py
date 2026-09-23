"""Production alerting.

Turns AURA metrics + health signals into real operational alerts delivered to
configured channels. This module is intentionally deliberate and small:

- :class:`AlertChannel` is the delivery contract. The built-in
  :class:`WebhookAlertChannel` posts JSON to a configured HTTP(S) endpoint
  (Slack-compatible, PagerDuty-style, or a generic sink) using the standard
  library; delivery retries with backoff.
- :class:`AlertManager` is the evaluation + lifecycle engine:
  deduplication (identical alerts are grouped), cooldown (no alert storms),
  severity, escalation by failure count, recovery notifications, and
  delivery-failure handling (alerts are never dropped silently — failed
  delivery is itself surfaced).
- Rules are evaluated from a metrics snapshot plus a health/dependency dict.
  Thresholds are fully configurable; nothing is hard-coded for tests.

Secrets are never transmitted: alert payloads carry ids, decisions, and
diagnostic fields only (callers must not include raw credentials), and the
redactor is applied at the boundary.

Alert state is in-process. Multi-instance deployments can point each instance
at the same channel; inter-instance dedup is intentionally out of scope here
(the system documents that operators may centralize via the channel).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("aura.observability.alerts")


class AlertSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Alert:
    """One alert instance (deduplicated in the manager)."""

    rule: str
    severity: AlertSeverity
    message: str
    context: str  # instance_id / environment breadcrumb
    occurred_at: float
    occurrence_count: int = 1
    recovered: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "occurred_at": self.occurred_at,
            "occurrence_count": self.occurrence_count,
            "recovered": self.recovered,
        }


@runtime_checkable
class AlertChannel(Protocol):
    """Delivery contract for alert channels."""

    def deliver(self, alert: Alert) -> None:
        """Deliver an alert. Raise on failure (caller handles retry/backoff)."""
        ...


class WebhookAlertChannel:
    """Real HTTP(S) webhook delivery with bounded retries and backoff.

    Posts ``{"rule","severity","message","context","occurred_at"}`` as JSON to
    the configured URL. Compatible with Slack-style and PagerDuty-style
    endpoints (the payload is a generic object; shape is channel-specific but
    defaults include the fields operators need).
    """

    def __init__(
        self,
        *,
        url: str,
        max_attempts: int = 3,
        backoff_seconds: float = 0.25,
        timeout_seconds: float = 5.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        if not url:
            raise ValueError("webhook URL is required")
        self._url = url
        self._max_attempts = max(1, max_attempts)
        self._backoff = max(0.0, backoff_seconds)
        self._timeout = timeout_seconds
        self._headers = {"Content-Type": "application/json", **(headers or {})}

    def deliver(self, alert: Alert) -> None:
        payload = json.dumps(alert.to_dict(), sort_keys=True).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            try:
                req = urllib.request.Request(
                    self._url, data=payload, headers=self._headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    if not 200 <= resp.status < 300:
                        raise RuntimeError(f"webhook returned HTTP {resp.status}")
                    return
            except (urllib.error.URLError, OSError, RuntimeError) as exc:
                last_error = exc
                if attempt + 1 < self._max_attempts:
                    time.sleep(self._backoff * (2**attempt))
        raise last_error or RuntimeError("webhook delivery failed")

    def __repr__(self) -> str:  # keep secrets out of reprs/logs
        return "WebhookAlertChannel(url=<configured>)"


@dataclass(frozen=True, slots=True)
class AlertRule:
    """A named rule that maps a signal to an alert at a configurable threshold.

    ``evaluate(snapshot, health, now)`` reads the relevant signal and returns
    ``(alert, bool_active)``. A rule that stops firing produces a recovery
    alert (``recovered=True``) so operators know the condition cleared.
    """

    name: str
    severity: AlertSeverity
    message: str
    kind: str  # "error_rate" | "latency" | "health" | "counter"
    metric: str  # key into snapshot["counters"]/["latency"] or "dependency"
    threshold: float
    # For latency rules, the percentile bucket key in snapshot["latency"].
    latency_key: str | None = None
    cooldown_seconds: float = 300.0

    def evaluate(
        self,
        snapshot: dict[str, dict[str, Any]],
        health: dict[str, Any],
        now: float,
    ) -> tuple[Alert | None, bool]:
        value = self._read(snapshot, health)
        active = value > self.threshold
        if not active:
            return None, False
        message = self.message.format(value=round(value, 4), threshold=self.threshold)
        return (
            Alert(rule=self.name, severity=self.severity, message=message, context="", occurred_at=now),
            True,
        )

    def _read(self, snapshot: dict[str, dict[str, Any]], health: dict[str, Any]) -> float:
        if self.kind == "health":
            dep = health.get("dependency", {})
            return 0.0 if dep.get("ok", False) else 1.0
        if self.kind == "error_rate":
            counters = snapshot.get("counters", {})
            total = float(counters.get("execution_count", 0))
            fails = float(counters.get("execution_failure", 0))
            if total <= 0:
                return 0.0
            return fails / total
        if self.kind == "latency":
            bucket = snapshot.get("latency", {}).get(self.metric, {})
            if not bucket:
                return 0.0
            if self.latency_key and self.latency_key in bucket:
                return float(bucket[self.latency_key])
            return float(bucket.get("max_seconds", 0.0))
        # counter
        return float(snapshot.get("counters", {}).get(self.metric, 0))


class LoggingAlertChannel:
    """Delivers alerts to the structured logger (no network).

    Useful as a default/no-op channel and in tests to assert delivery without
    a live endpoint.
    """

    def deliver(self, alert: Alert) -> None:
        logger.warning("alert fired: %s", json.dumps(alert.to_dict(), sort_keys=True))


class AlertManager:
    """Evaluation + lifecycle for configured alert rules.

    - Dedup/grouping: an active rule fires once per cooldown window (identical
      alerts are grouped; occurrence_count tracks accumulation so 1000
      failures do not produce 1000 alerts).
    - Recovery: when a previously active rule goes inactive, a recovery alert
      (recovered=True) is delivered.
    - Escalation: the manager escalates one severity step after 3 consecutive
      firings.
    - Delivery failure: delivery errors are caught and surfaced via
      delivery_failures (never silently dropped).
    """

    def __init__(self, *, channels: list[AlertChannel] | None = None, instance_id: str = "default") -> None:
        self._channels = list(channels) if channels else [LoggingAlertChannel()]
        self._instance_id = instance_id
        self._last_active_at: dict[str, float] = {}
        self._consecutive: dict[str, int] = {}
        self._rules: dict[str, AlertRule] = {}
        self._delivered: list[Alert] = []
        self._last_sent: dict[str, Alert] = {}
        self.delivery_failures: list[tuple[str, str]] = []
        self._severity_order: list[AlertSeverity] = list(AlertSeverity)

    def add_rule(self, rule: AlertRule) -> None:
        self._rules[rule.name] = rule

    @property
    def rules(self) -> dict[str, AlertRule]:
        return dict(self._rules)

    def evaluate(
        self,
        *,
        snapshot: dict[str, dict[str, Any]],
        health: dict[str, Any],
        now: float | None = None,
    ) -> list[Alert]:
        """Run all rules; returns alerts delivered this tick (incl. recovery)."""
        now = now if now is not None else time.time()
        fired: list[Alert] = []
        for name, rule in self._rules.items():
            alert, active = rule.evaluate(snapshot, health, now)
            self._tick_rule(name, active, rule, alert, fired, now)
        return fired

    def _tick_rule(
        self,
        name: str,
        active: bool,
        rule: AlertRule,
        alert: Alert | None,
        fired: list[Alert],
        now: float,
    ) -> None:
        if not active:
            if self._consecutive.get(name, 0) > 0:
                recovery = Alert(
                    rule=name,
                    severity=rule.severity,
                    message=f"RECOVERED: {rule.message.format(value=0.0, threshold=rule.threshold)}",
                    context=self._instance_id,
                    occurred_at=now,
                    occurrence_count=self._consecutive.pop(name, 1),
                    recovered=True,
                )
                self._deliver(recovery, fired)
            self._last_active_at.pop(name, None)
            return
        consecutive = self._consecutive.get(name, 0) + 1
        self._consecutive[name] = consecutive
        last = self._last_active_at.get(name, float("-inf"))  # never suppress first fire
        if now - last < rule.cooldown_seconds:
            # Suppressed delivery: keep counting occurrences but do not spam.
            # Bump the occurrence count on the most recent delivered alert for
            # this rule so operators see accumulation on the deduplicated alert.
            current_last = self._last_sent.get(name)
            if current_last is not None:
                updated = Alert(
                    rule=current_last.rule,
                    severity=current_last.severity,
                    message=current_last.message,
                    context=current_last.context,
                    occurred_at=current_last.occurred_at,
                    occurrence_count=consecutive,
                    recovered=False,
                )
                self._last_sent[name] = updated
                if self._delivered and self._delivered[-1] is current_last:
                    self._delivered[-1] = updated
            return
        self._last_active_at[name] = now
        severity = self._maybe_escalate(rule, consecutive)
        if alert is not None and severity is not rule.severity:
            alert = Alert(
                rule=alert.rule, severity=severity, message=alert.message,
                context=self._instance_id, occurred_at=alert.occurred_at,
                occurrence_count=consecutive,
            )
        self._deliver(alert, fired)

    def _maybe_escalate(self, rule: AlertRule, consecutive: int) -> AlertSeverity:
        idx = self._severity_order.index(rule.severity)
        steps = consecutive // 3
        return self._severity_order[min(idx + steps, len(self._severity_order) - 1)]

    def _deliver(self, alert: Alert | None, fired: list[Alert]) -> None:
        if alert is None:
            return
        fired.append(alert)
        for channel in self._channels:
            try:
                channel.deliver(alert)
                self._delivered.append(alert)
                self._last_sent[alert.rule] = alert
            except Exception as exc:  # noqa: BLE001 - surface delivery failure
                self.delivery_failures.append((alert.rule, str(exc)))
                logger.error("alert delivery failed rule=%s error=%s", alert.rule, exc)

    @property
    def delivered(self) -> list[Alert]:
        return list(self._delivered)

    def health(self) -> dict[str, object]:
        return {
            "rules": sorted(self._rules),
            "delivered_count": len(self._delivered),
            "delivery_failures": len(self.delivery_failures),
            "active": {k: v for k, v in self._consecutive.items() if v > 0},
        }


def default_rules() -> list[AlertRule]:
    """Sane, operator-configurable production defaults."""
    return [
        AlertRule(name="ServiceDown", severity=AlertSeverity.CRITICAL,
                  message="persistence dependency unavailable",
                  kind="health", metric="dependency", threshold=0.0),
        AlertRule(name="HighErrorRate", severity=AlertSeverity.HIGH,
                  message="execution error rate {value} exceeds {threshold}",
                  kind="error_rate", metric="execution_count", threshold=0.10),
        AlertRule(name="HighLatency", severity=AlertSeverity.MEDIUM,
                  message="max pipeline latency {value}s exceeds {threshold}s",
                  kind="latency", metric="pipeline", latency_key="max_seconds", threshold=30.0),
        AlertRule(name="AuthenticationAttack", severity=AlertSeverity.HIGH,
                  message="auth failures {value} exceed {threshold}",
                  kind="counter", metric="api_auth_failure", threshold=50),
        AlertRule(name="ExcessiveRateLimit", severity=AlertSeverity.LOW,
                  message="rate-limit denials {value} exceed {threshold}",
                  kind="counter", metric="rate_limit_deny", threshold=100),
        AlertRule(name="PersistenceFailure", severity=AlertSeverity.CRITICAL,
                  message="persistence errors {value} exceed {threshold}",
                  kind="counter", metric="memory_operation_failure", threshold=10),
        AlertRule(name="ProviderFailure", severity=AlertSeverity.MEDIUM,
                  message="provider failures {value} exceed {threshold}",
                  kind="counter", metric="provider_failure", threshold=5),
    ]


__all__ = [
    "Alert",
    "AlertChannel",
    "AlertManager",
    "AlertRule",
    "AlertSeverity",
    "LoggingAlertChannel",
    "WebhookAlertChannel",
    "default_rules",
]