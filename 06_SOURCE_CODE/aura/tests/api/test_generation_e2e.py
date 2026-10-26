"""Phase 2B: normal chat reaches a configured generation provider end-to-end.

Uses a real local OpenAI-compatible ``/chat/completions`` endpoint so the full
canonical path (HTTP -> /v1/reason -> Brain -> ReasoningEngine -> ProviderManager
-> adapter -> HTTP) is exercised, not mocked. Also proves honest failure when
the provider is down and credential non-leakage.
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.config.settings import AuraConfig, ProviderConfig, StorageConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura

GENERATED = "Artificial intelligence and machine learning are related fields of computer science."


class _CompletionsHandler(BaseHTTPRequestHandler):
    last_body: dict | None = None
    last_auth: str | None = None

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        _CompletionsHandler.last_body = json.loads(raw.decode("utf-8"))
        _CompletionsHandler.last_auth = self.headers.get("Authorization")
        payload = json.dumps({"choices": [{"message": {"content": GENERATED}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: object) -> None:  # silence test noise
        pass


@pytest.fixture
def mock_provider() -> int:
    _CompletionsHandler.last_body = None
    _CompletionsHandler.last_auth = None
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _CompletionsHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_port
    httpd.shutdown()


def _config(port: int, *, enabled: bool = True, down: bool = False) -> AuraConfig:
    return AuraConfig(
        storage=StorageConfig(backend="memory"),
        provider=ProviderConfig(
            enabled=enabled,
            name="local-test",
            kind="openai",
            base_url=f"http://127.0.0.1:{port if not down else 9}/v1",
            model="test-model",
            api_key="sk-test-secret",
            privacy_approved=True,
            timeout_seconds=3.0,
        ),
    )


def _post(port: int, path: str, payload: dict) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=20)
    conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def _start_server(cfg: AuraConfig) -> tuple[AuraApiServer, int]:
    api = AuraApiServer(
        aura=Aura(config=cfg, clock=ManualClock(0), seed=1),
        config=ServerConfig(host="127.0.0.1", port=0),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd
    return api, httpd.server_port


def _post_auth(port: int, path: str, payload: dict, token: str) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=20)
    conn.request(
        "POST",
        path,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def _issue_key(port: int, *scopes: str) -> str:
    status, body = _post_auth(port, "/v1/keys", {"scopes": list(scopes)}, "admin-secret-key-16+")
    assert status == 201, body
    return str(body["api_key"])


def test_general_knowledge_reaches_generation_provider(mock_provider: int) -> None:
    _api, port = _start_server(_config(mock_provider))
    status, body = _post(port, "/v1/reason", {"question": "Explain artificial intelligence and machine learning."})
    assert status == 200
    # The generated (provider) answer is surfaced, not a fabricated abstention.
    assert body.get("answer") == GENERATED
    assert body.get("provider", {}).get("status") == "ok"
    assert body.get("provider", {}).get("mode") == "generation"
    # The provider was actually consulted with the credential header (never echoed).
    assert _CompletionsHandler.last_body is not None
    assert _CompletionsHandler.last_auth == "Bearer sk-test-secret"
    rendered = json.dumps(body)
    assert "sk-test-secret" not in rendered, "credential leaked into the API response"


def test_generation_carries_conversation_history(mock_provider: int) -> None:
    _api, port = _start_server(_config(mock_provider))
    history = [{"role": "user", "content": "Earlier we discussed machine learning."}]
    status, body = _post(port, "/v1/reason", {"question": "What are its three major types?", "history": history})
    assert status == 200 and body.get("answer") == GENERATED
    sent = json.dumps(_CompletionsHandler.last_body or {})
    assert "Earlier we discussed machine learning." in sent, "conversation history not sent to provider"


def test_provider_down_is_honest(port_factory=5) -> None:
    _api, port = _start_server(_config(9999, down=True))
    status, body = _post(port, "/v1/reason", {"question": "Explain quantum gravity."})
    assert status == 200
    # Honest failure: never a fabricated answer.
    provider = body.get("provider", {})
    assert provider.get("status") in {"unavailable", "timeout", "not_configured"}
    assert body.get("answer") == "I do not know", "fabricated an answer for an unreachable provider"
    assert "sk-test-secret" not in json.dumps(body), "credential leaked on provider failure"


def test_disabled_provider_never_generates(mock_provider: int) -> None:
    _api, port = _start_server(_config(mock_provider, enabled=False))
    status, body = _post(port, "/v1/reason", {"question": "Explain artificial intelligence."})
    assert status == 200
    assert body.get("answer") == "I do not know"
    assert body.get("provider", {}).get("status") == "not_configured"


def test_without_providers_use_scope_generation_is_denied(mock_provider: int) -> None:
    """A boundary without the providers.use scope must never reach the model."""
    cfg = _config(mock_provider)
    api = AuraApiServer(
        aura=Aura(config=cfg, clock=ManualClock(0), seed=1),
        config=ServerConfig(
            host="127.0.0.1", port=0, api_key="service-secret-key-16+", admin_key="admin-secret-key-16+"
        ),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd
    port = httpd.server_port

    # A key with cognition.reason but NOT providers.use is denied at the boundary.
    key = _issue_key(port, "cognition.reason")
    status, body = _post_auth(port, "/v1/reason", {"question": "Explain AI and ML."}, key)
    assert status == 403 and body.get("error", {}).get("code") == "api.provider_forbidden"
    assert _CompletionsHandler.last_body is None, "provider was reached without authorization"

    # With providers.use (plus cognition.reason) the boundary allows generation.
    key2 = _issue_key(port, "cognition.reason", "providers.use")
    status, body = _post_auth(port, "/v1/reason", {"question": "Explain AI and ML."}, key2)
    assert status == 200 and body.get("answer") == GENERATED