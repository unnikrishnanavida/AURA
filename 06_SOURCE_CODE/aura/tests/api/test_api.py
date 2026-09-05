"""API service tests: health, readiness, reason, replay, validation, correlation ids."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura


@pytest.fixture
def server() -> AuraApiServer:
    aura = Aura(clock=ManualClock(0), seed=3)
    return AuraApiServer(aura=aura, config=ServerConfig(host="127.0.0.1", port=0))


def _start(api: AuraApiServer) -> int:
    from http.server import ThreadingHTTPServer

    wrapped = api._handler()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), wrapped)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    api._httpd = httpd
    return httpd.server_port


def _get(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    del token
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body


def _post(port: int, path: str, payload: dict) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body


@pytest.fixture
def port(server: AuraApiServer) -> int:
    return _start(server)


def test_health_endpoint(port: int) -> None:
    status, body = _get(port, "/health")
    assert status == 200
    assert body["status"] == "ok"


def test_ready_endpoint(port: int) -> None:
    status, body = _get(port, "/ready")
    assert status == 200
    assert body["status"] in {"ready", "not_ready"}


def test_reason_endpoint(port: int) -> None:
    status, body = _post(port, "/v1/reason", {"question": "is this an api?"})
    assert status == 200
    assert "execution_id" in body
    assert "answer" in body


def test_reason_validation_missing_question(port: int) -> None:
    status, body = _post(port, "/v1/reason", {})
    assert status == 400
    assert body["error"]["code"] == "api.validation"


def test_reason_invalid_json(port: int) -> None:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", "/v1/reason", body=b"not json", headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    assert response.status == 400
    assert body["error"]["code"] in {"api.invalid_json", "api.error"}


def test_openapi(port: int) -> None:
    status, body = _get(port, "/openapi.json")
    assert status == 200
    assert body["openapi"].startswith("3.")


def test_unknown_route(port: int) -> None:
    status, body = _get(port, "/nope")
    assert status == 404


def test_replay_endpoint(port: int, server: AuraApiServer) -> None:
    result = server.aura.reason("record now", facts={"z": 0.9})
    execution_id = result["execution_id"]
    status, body = _get(port, f"/v1/replay/{execution_id}")
    assert status == 200
    assert body["events"]