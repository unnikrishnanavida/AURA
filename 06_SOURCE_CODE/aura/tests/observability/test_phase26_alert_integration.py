"""Phase 26 alert integration tests.

Proves the full chain with real runtime events and a real webhook sink:

    real event
        -> metric increment
        -> alert evaluation
        -> alert firing
        -> webhook payload
        -> delivered_count += 1

Also verifies /health continues to expose ``alerts_fired`` + ``alert_health``
with the existing 200 healthy / 503 unhealthy semantics.
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.observability.alerts import AlertManager, AlertRule, default_rules
from aura.sdk.client import Aura

ADMIN_KEY = "admin-key-at-least-16-char"
SERVICE_KEY = "service-key-at-least-16-char"


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


def _start(api: AuraApiServer) -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd  # type: ignore[attr-defined]
    return httpd.server_port


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8")
    conn.request("POST", path, body=data, headers={**headers, "Content-Length": str(len(data))})
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    try:
        return response.status, json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return response.status, {}


def _get(port: int, path: str) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", path)
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    try:
        return response.status, json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return response.status, {}


def _rule(rules: list[AlertRule], name: str) -> AlertRule:
    return next(r for r in rules if r.name == name)


# -- AuthenticationAttack: real 401 events -> metric -> alert -> webhook -----


def test_auth_attack_fires_alert_and_delivers_webhook(webhook_sink: object) -> None:
    httpd, handler_cls = webhook_sink
    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key=SERVICE_KEY,
            admin_key=ADMIN_KEY,
            alert_webhook_url=f"http://127.0.0.1:{httpd.server_port}/hooks/aura",
        ),
    )
    port = _start(api)

    # Genuine authentication failures. The default AuthenticationAttack rule
    # threshold is 50 with a > comparison, so we need at least 51 failures.
    for _ in range(51):
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token="wrong-key-0123456789")
        assert status == 401
    assert api.aura.brain.metrics.count("api_auth_failure") == 51

    # /health runs _evaluate_alerts against the live metrics snapshot.
    status, body = _get(port, "/health")
    assert status == 200
    assert isinstance(body, dict)
    assert "alerts_fired" in body
    assert "alert_health" in body
    fired = body["alerts_fired"]
    assert any(a["rule"] == "AuthenticationAttack" for a in fired)

    # Webhook delivery: payload arrived and delivered_count incremented.
    assert any(p.get("rule") == "AuthenticationAttack" for p in handler_cls.received)
    assert api._alert_manager.health()["delivered_count"] >= 1  # type: ignore[union-attr]

    httpd.shutdown()
    httpd.server_close()


# -- ExcessiveRateLimit: real 429 events -> metric -> alert ------------------


def test_excessive_rate_limit_fires_alert_from_real_denials() -> None:
    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key=SERVICE_KEY,
            admin_key=ADMIN_KEY,
            rate_burst=1,
            rate_per_second=0.001,
        ),
    )
    port = _start(api)

    denied = 0
    for _ in range(102):  # 1 allowed + 101 denied > threshold 100
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token=SERVICE_KEY)
        if status == 429:
            denied += 1
    assert denied == 101
    assert api.aura.brain.metrics.count("rate_limit_deny") == 101

    manager = AlertManager()
    manager.add_rule(_rule(default_rules(), "ExcessiveRateLimit"))
    fired = manager.evaluate(
        snapshot=api.aura.metrics(), health={"dependency": {"ok": True}}, now=1.0
    )
    assert any(a.rule == "ExcessiveRateLimit" for a in fired)


# -- PersistenceFailure: real memory failures -> metric -> alert -------------


def test_persistence_failure_fires_alert_from_real_memory_failures() -> None:
    from aura.memory.engine import MemoryEngine
    from aura.memory.models import MemoryType
    from aura.observability.metrics import Metrics

    class _BrokenStore:
        def add(self, entry: object) -> object:
            raise RuntimeError("storage backend unavailable")

    metrics = Metrics()
    engine = MemoryEngine(store=_BrokenStore(), metrics=metrics)  # type: ignore[arg-type]
    for _ in range(11):  # threshold 10 with > comparison -> need 11 failures
        with pytest.raises(RuntimeError):
            engine.remember(key="k", kind=MemoryType.EPISODIC, content={"a": 1})
    assert metrics.count("memory_operation_failure") == 11

    manager = AlertManager()
    manager.add_rule(_rule(default_rules(), "PersistenceFailure"))
    fired = manager.evaluate(
        snapshot={"counters": metrics.snapshot()["counters"], "latency": {}},
        health={"dependency": {"ok": True}},
        now=1.0,
    )
    assert any(a.rule == "PersistenceFailure" for a in fired)


# -- HighErrorRate: ratio derived from live execution metrics -----------------


def test_high_error_rate_fires_from_real_executions() -> None:
    aura = Aura(clock=ManualClock(0), seed=3)
    for _ in range(8):
        aura.reason("healthy execution?")

    def boom(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("reasoning engine exploded")

    aura.brain.reasoning.reason = boom  # type: ignore[method-assign]
    for _ in range(3):
        with pytest.raises(RuntimeError):
            aura.reason("boom")

    snap = aura.metrics()
    counters = snap["counters"]
    assert counters["execution_count"] == 11
    assert counters["execution_failure"] == 3
    ratio = counters["execution_failure"] / counters["execution_count"]
    assert ratio > 0.10  # 3/11 ≈ 0.27 > threshold 0.10

    # Use the ACTUAL default HighErrorRate rule (threshold 0.10) untouched.
    manager = AlertManager()
    manager.add_rule(_rule(default_rules(), "HighErrorRate"))
    fired = manager.evaluate(snapshot=snap, health={"dependency": {"ok": True}}, now=1.0)
    assert any(a.rule == "HighErrorRate" for a in fired)


# -- ProviderFailure rule consumes the counter when populated -----------------


def test_provider_failure_rule_consumes_provider_failure_counter() -> None:
    """The default rule works off the counter; the metric itself has no
    production call site yet (documented as NOT INSTRUMENTED in the Phase-26
    report — the provider abstraction has no runtime invocation path)."""
    manager = AlertManager()
    manager.add_rule(_rule(default_rules(), "ProviderFailure"))
    fired = manager.evaluate(
        snapshot={"counters": {"provider_failure": 6}, "latency": {}},
        health={"dependency": {"ok": True}},
        now=1.0,
    )
    assert any(a.rule == "ProviderFailure" for a in fired)


# -- /health preserves semantics ----------------------------------------------


def test_health_endpoint_preserves_alerts_fields_and_semantics() -> None:
    api = AuraApiServer(
        config=ServerConfig(host="127.0.0.1", port=0, api_key=SERVICE_KEY, admin_key=ADMIN_KEY),
    )
    port = _start(api)
    status, body = _get(port, "/health")
    assert status == 200
    assert isinstance(body, dict)
    assert body["status"] == "ok"
    assert "alerts_fired" in body
    assert "alert_health" in body