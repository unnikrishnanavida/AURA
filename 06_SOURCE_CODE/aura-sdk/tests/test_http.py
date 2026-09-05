"""HTTP transport integration tests against the canonical AURA API server."""

from __future__ import annotations

import sys
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aura" / "src"))

from aura_sdk import AuraSDK, SdkConfig  # noqa: E402
from aura_sdk.config import TransportMode  # noqa: E402
from aura_sdk.errors import ApiError  # noqa: E402

TEST_KEY = "test-api-key-123456"


@pytest.fixture
def server() -> tuple[str, int, object]:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.foundation.clock import ManualClock
    from aura.sdk.client import Aura as CanonicalAura

    aura = CanonicalAura(clock=ManualClock(0), seed=3)
    api = AuraApiServer(
        aura=aura,
        config=ServerConfig(host="127.0.0.1", port=0, api_key=TEST_KEY, allow_pipeline=True),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return "127.0.0.1", httpd.server_port, api


def _shutdown(port: int) -> None:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", "/v1/sessions")
    conn.getresponse()
    conn.close()


@pytest.fixture
def port(server: tuple[str, int, object]) -> int:
    return server[1]


@pytest.fixture
def sdk(port: int) -> AuraSDK:
    return AuraSDK(
        config=SdkConfig(
            mode=TransportMode.HTTP,
            endpoint=f"http://127.0.0.1:{port}",
            api_key=TEST_KEY,
            timeout_seconds=10,
        )
    )


def test_http_health(sdk: AuraSDK) -> None:
    assert sdk.health()["status"] == "ok"


def test_http_reason(sdk: AuraSDK) -> None:
    result = sdk.reason("is the API working?", facts={"z": 0.9})
    assert "answer" in result


def test_http_remember_recall(sdk: AuraSDK) -> None:
    memory_id = sdk.remember("http-note", {"text": "hello"})
    entries = sdk.recall("http-note")
    assert entries and entries[0]["key"] == "http-note"
    assert memory_id


def test_http_auth_failure(port: int) -> None:
    bad = AuraSDK(
        config=SdkConfig(
            mode=TransportMode.HTTP,
            endpoint=f"http://127.0.0.1:{port}",
            api_key="incorrect-key-987654",
        )
    )
    response = bad.execute("reason", {"question": "x"})
    assert not response.ok
    assert isinstance(response.error, ApiError)
    assert response.error.http_status == 401


def test_http_api_error_surfaces_code(sdk: AuraSDK) -> None:
    response = sdk.execute("reason", {"question": ""})
    assert not response.ok
    assert response.error is not None
    assert "question" in response.error.message