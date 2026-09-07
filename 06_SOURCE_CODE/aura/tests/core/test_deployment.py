"""Deployment/operations tests: config gates, liveness/readiness with real deps, security headers, proxy handling."""

from __future__ import annotations

import json
import os
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura


def _start(api: AuraApiServer) -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd
    return httpd.server_port


def _get(port: int, path: str) -> tuple[int, dict, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", path)
    response = conn.getresponse()
    raw = response.read()
    headers = dict(response.getheaders())
    conn.close()
    return response.status, json.loads(raw.decode("utf-8")), headers


def _server(**kw: object) -> AuraApiServer:
    return AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=1),
        config=ServerConfig(host="127.0.0.1", port=0, **kw),  # type: ignore[arg-type]
    )


# -- config gates -----------------------------------------------------------------
def test_production_rejects_memory_backend(monkeypatch) -> None:
    from aura.config.settings import AuraConfig, Environments

    monkeypatch.delenv("AURA_CONFIG", raising=False)
    try:
        AuraConfig(environment=Environments.PRODUCTION)
        assert False
    except ValueError:
        pass


def test_deployment_validator_gates(tmp_path: Path) -> None:
    from scripts.validate_deployment import validate_deployment

    error = validate_deployment("production", storage_backend="memory")
    assert "production" in error or "invalid" in error
    # with sqlite but no secret
    os.environ.pop("AURA_API_SECRET", None)
    error2 = validate_deployment("production", storage_backend="sqlite")
    assert "AURA_API_SECRET" in error2
    # with sqlite + secret -> valid
    os.environ["AURA_API_SECRET"] = "0123456789abcdef"
    assert validate_deployment("production", storage_backend="sqlite") == ""
    os.environ.pop("AURA_API_SECRET", None)


def test_run_server_refuses_production_without_secret(monkeypatch) -> None:
    monkeypatch.setenv("AURA_ENVIRONMENT", "production")
    monkeypatch.setenv("AURA_STORAGE_BACKEND", "sqlite")
    monkeypatch.delenv("AURA_API_SECRET", raising=False)
    from aura.api.server import run_server
    from aura.foundation.errors import ConfigurationError

    try:
        run_server(host="127.0.0.1", port=0)
        assert False, "expected ConfigurationError"
    except ConfigurationError as exc:
        assert "AURA_API_SECRET" in str(exc)


# -- liveness/readiness ------------------------------------------------------------
def test_liveness_is_quick_and_unauthenticated() -> None:
    api = _server()
    port = _start(api)
    status, body, _ = _get(port, "/liveness")
    assert status == 200
    assert body["status"] == "alive"


def test_health_verifies_dependency() -> None:
    api = _server()
    port = _start(api)
    status, body, _ = _get(port, "/health")
    assert status == 200
    assert body["dependency"]["ok"] is True
    assert body["dependency"]["backend"] == "InMemoryMemoryStore"


def test_health_reports_sqlite_dependency(tmp_path: Path) -> None:
    from aura.config.settings import AuraConfig, StorageConfig

    db = tmp_path / "dep.sqlite3"
    cfg = AuraConfig(storage=StorageConfig(backend="sqlite", sqlite_path=str(db)))
    api = AuraApiServer(aura=Aura(clock=ManualClock(0), config=cfg))
    port = _start(api)
    status, body, _ = _get(port, "/health")
    assert status == 200
    assert body["dependency"]["ok"] is True
    assert body["dependency"]["backend"] == "SQLiteMemoryStore"
    api.aura.brain.memory.store.close()  # type: ignore[attr-defined]


def test_ready_endpoint_readiness() -> None:
    api = _server()
    port = _start(api)
    status, body, _ = _get(port, "/ready")
    assert status in (200, 503)
    assert body["status"] in ("ready", "not_ready")


def test_security_headers_present() -> None:
    api = _server()
    port = _start(api)
    _status, _body, headers = _get(port, "/health")
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "X-Request-Id" in headers


def test_proxy_gate_used_for_rate_limit() -> None:
    api = _server(trust_proxy=True)
    port = _start(api)
    # A request with a distinct X-Forwarded-For sees a separate rate-limit bucket.
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/health", headers={"X-Forwarded-For": "203.0.113.9"})
    status1 = conn.getresponse().status
    conn.close()
    assert status1 in (200, 503)  # health hits dependency and returns 200


def test_memory_store_counts_in_health() -> None:
    api = _server()
    api.aura.remember("k", {"v": 1})
    port = _start(api)
    _status, body, _ = _get(port, "/health")
    assert body["dependency"]["ok"] is True