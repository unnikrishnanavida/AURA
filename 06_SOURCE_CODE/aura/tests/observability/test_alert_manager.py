"""AlertManager rule/lifecycle tests (Phase 26)."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.observability.alerts import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    WebhookAlertChannel,
    default_rules,
)


class _SinkHandler(BaseHTTPRequestHandler):
    received: list[dict] = []

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        self.__class__.received.append({"raw": raw.decode()})
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


@pytest.fixture()
def webhook_sink() -> tuple[ThreadingHTTPServer, object]:
    _SinkHandler.received = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _SinkHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, _SinkHandler


def _healthy() -> dict[str, object]:
    return {"dependency": {"ok": True, "backend": "test"}}


def test_service_down_triggers_critical_alert(webhook_sink: object) -> None:
    httpd, handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(default_rules()[0])  # ServiceDown
    manager.evaluate(
        snapshot={"counters": {}, "latency": {}},
        health={"dependency": {"ok": False, "backend": "test"}},
        now=100.0,
    )
    assert len(handler_cls.received) == 1
    assert manager.delivered[0].rule == "ServiceDown"
    assert manager.delivered[0].severity == AlertSeverity.CRITICAL
    httpd.shutdown()
    httpd.server_close()


def test_cooldown_dedup_prevents_alert_storms(webhook_sink: object) -> None:
    httpd, handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(AlertRule(
        name="Flap", severity=AlertSeverity.HIGH, message="x", kind="counter",
        metric="fails", threshold=0, cooldown_seconds=600.0,
    ))
    for t in (1.0, 2.0, 3.0, 4.0):
        manager.evaluate(snapshot={"counters": {"fails": t}, "latency": {}}, health=_healthy(), now=t)
    assert len(handler_cls.received) == 1  # cooldown suppressed the rest
    assert manager.delivered[0].occurrence_count == 4  # but accumulation tracked
    httpd.shutdown()
    httpd.server_close()


def test_recovery_notification(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(AlertRule(
        name="Down", severity=AlertSeverity.CRITICAL, message="dep", kind="health",
        metric="dependency", threshold=0.0, cooldown_seconds=0.0,
    ))
    manager.evaluate(snapshot={}, health={"dependency": {"ok": False}}, now=1.0)
    manager.evaluate(snapshot={}, health={"dependency": {"ok": True}}, now=2.0)
    recovered = [a for a in manager.delivered if a.recovered]
    assert len(recovered) == 1
    assert recovered[0].rule == "Down"
    httpd.shutdown()
    httpd.server_close()
def test_severity_escalation_after_repeated_firings(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(AlertRule(
        name="Error", severity=AlertSeverity.LOW, message="e", kind="counter",
        metric="fails", threshold=0, cooldown_seconds=0.0,
    ))
    for t in (1.0, 2.0, 3.0, 4.0):
        manager.evaluate(snapshot={"counters": {"fails": t}, "latency": {}}, health=_healthy(), now=t)
    severities = [a.severity for a in manager.delivered]
    assert AlertSeverity.LOW in severities
    assert any(s != AlertSeverity.LOW for s in severities)  # escalated
    httpd.shutdown()
    httpd.server_close()


def test_default_manager_uses_logging_channel() -> None:
    manager = AlertManager()
    manager.add_rule(AlertRule(
        name="Down", severity=AlertSeverity.CRITICAL, message="dep", kind="health",
        metric="dependency", threshold=0.0, cooldown_seconds=0.0,
    ))
    fired = manager.evaluate(snapshot={}, health={"dependency": {"ok": False}}, now=1.0)
    assert len(fired) == 1
    assert manager.health()["delivered_count"] == 1


def test_error_rate_rule(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(AlertRule(
        name="HighErrorRate", severity=AlertSeverity.HIGH, message="er {value}", kind="error_rate",
        metric="execution_count", threshold=0.10, cooldown_seconds=0.0,
    ))
    fired = manager.evaluate(
        snapshot={"counters": {"execution_count": 100, "execution_failure": 40}, "latency": {}},
        health=_healthy(), now=1.0,
    )
    assert len(fired) == 1
    assert fired[0].rule == "HighErrorRate"
    httpd.shutdown()
    httpd.server_close()


def test_latency_rule(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    manager = AlertManager(channels=[WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/h")])
    manager.add_rule(AlertRule(
        name="HighLatency", severity=AlertSeverity.MEDIUM, message="lat {value}", kind="latency",
        metric="pipeline", latency_key="max_seconds", threshold=30.0, cooldown_seconds=0.0,
    ))
    fired = manager.evaluate(
        snapshot={"counters": {}, "latency": {"pipeline": {"max_seconds": 45.0, "count": 1}}},
        health=_healthy(), now=1.0,
    )
    assert len(fired) == 1
    assert fired[0].rule == "HighLatency"
    httpd.shutdown()
    httpd.server_close()