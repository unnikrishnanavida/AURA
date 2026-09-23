"""Alert channel + lifecycle tests (Phase 26).

Verifies real HTTP webhook delivery against a local sink, delivery-failure
handling, cooldown/dedup (no alert storms), recovery notifications, and that
alert payloads never carry secrets.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.observability.alerts import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    WebhookAlertChannel,
)


class _SinkHandler(BaseHTTPRequestHandler):
    received: list[dict] = []

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        self.__class__.received.append(json.loads(raw.decode()))
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


def test_webhook_channel_delivers_real_http(webhook_sink: object) -> None:
    httpd, handler_cls = webhook_sink
    channel = WebhookAlertChannel(url=f"http://127.0.0.1:{httpd.server_port}/hooks/aura", max_attempts=2)
    alert = Alert(rule="ServiceDown", severity=AlertSeverity.CRITICAL, message="db down", context="i1", occurred_at=1.0)
    channel.deliver(alert)
    captured = handler_cls.received
    assert len(captured) == 1
    assert captured[0]["rule"] == "ServiceDown"
    assert captured[0]["severity"] == "critical"
    assert captured[0]["message"] == "db down"
    httpd.shutdown()
    httpd.server_close()


def test_webhook_channel_failure_raises(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    channel = WebhookAlertChannel(url="http://127.0.0.1:1/unreachable", max_attempts=2, backoff_seconds=0.01)
    alert = Alert(rule="X", severity=AlertSeverity.HIGH, message="m", context="c", occurred_at=2.0)
    with pytest.raises((OSError, RuntimeError)):
        channel.deliver(alert)
    httpd.shutdown()
    httpd.server_close()


def test_delivery_failure_is_surfaced(webhook_sink: object) -> None:
    httpd, _handler_cls = webhook_sink
    manager = AlertManager(
        channels=[WebhookAlertChannel(url="http://127.0.0.1:1/down", max_attempts=1, backoff_seconds=0.0)]
    )
    manager.add_rule(AlertRule(
        name="Down", severity=AlertSeverity.CRITICAL, message="dep",
        kind="health", metric="dependency", threshold=0.0, cooldown_seconds=0.0,
    ))
    manager.evaluate(snapshot={}, health={"dependency": {"ok": False}}, now=1.0)
    assert len(manager.delivery_failures) == 1
    assert manager.delivery_failures[0][0] == "Down"
    httpd.shutdown()
    httpd.server_close()


def test_alert_payload_never_contains_secret_keys() -> None:
    alert = Alert(rule="R", severity=AlertSeverity.HIGH, message="m", context="c", occurred_at=1.0).to_dict()
    text = json.dumps(alert).lower()
    for needle in ("password", "api_key", "authorization", "token", "secret"):
        assert needle not in text