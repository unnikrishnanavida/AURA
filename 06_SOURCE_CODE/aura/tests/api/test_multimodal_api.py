"""Phase 1J HTTP integration: `/v1/agents/run` accepts optional multimodal
observations, reports each attachment honestly, and forwards only accepted
observations into the guarded agent run.
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.input.multimodal import CAPABILITY_UNAVAILABLE
from aura.sdk.client import Aura


@pytest.fixture
def server() -> AuraApiServer:
    return AuraApiServer(aura=Aura(clock=ManualClock(0), seed=3), config=ServerConfig(host="127.0.0.1", port=0))


@pytest.fixture
def port(server: AuraApiServer) -> int:
    wrapped = server._handler()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), wrapped)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    server._httpd = httpd
    return httpd.server_port


def _post(port: int, path: str, payload: dict) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body


def test_run_agent_with_mixed_observations_reports_honestly(port: int) -> None:
    status, body = _post(
        port,
        "/v1/agents/run",
        {
            "goal": "echo-world",
            "capabilities": ["echo"],
            "observations": [
                {
                    "media_type": "text/plain",
                    "content": "The blueprints are in the archive.",
                    "file_name": "note.txt",
                },
                {"media_type": "image/png", "content": "", "file_name": "photo.png"},
                {"media_type": "video/mp4", "content": "", "file_name": "clip.mp4"},
            ],
        },
    )

    assert status == 200
    report = body["observations_report"]
    assert len(report) == 3

    accepted = [e for e in report if e["status"] == "accepted"]
    unavailable = [e for e in report if e["status"] == CAPABILITY_UNAVAILABLE]
    assert len(accepted) == 1
    assert len(unavailable) == 2
    assert {e["modality"] for e in unavailable} == {"image", "video"}
    assert accepted[0]["modality"] == "text"
    assert accepted[0]["observation_id"]

    # Exactly the one accepted observation is forwarded, attributed + unverified.
    assert len(body["observations"]) == 1
    fwd = body["observations"][0]
    assert fwd["modality"] == "text"
    assert fwd["verified"] is False
    assert fwd["observation_id"] == accepted[0]["observation_id"]
    assert fwd["content"] == "The blueprints are in the archive."


def test_run_agent_without_observations_is_unchanged(port: int) -> None:
    status, body = _post(
        port,
        "/v1/agents/run",
        {"goal": "echo-world", "capabilities": ["echo"]},
    )
    assert status == 200
    assert body["observations_report"] == []
    assert body["observations"] == []


def test_run_agent_survives_no_capabilities(port: int) -> None:
    """Observations are optional metadata; they never inject a capability."""
    status, body = _post(
        port,
        "/v1/agents/run",
        {"goal": "echo-world", "capabilities": ["echo"], "observations": []},
    )
    assert status == 200


def test_run_agent_rejects_non_list_observations(port: int) -> None:
    status, body = _post(
        port,
        "/v1/agents/run",
        {"goal": "echo-world", "capabilities": ["echo"], "observations": {"media_type": "text/plain"}},
    )
    assert status == 400
    assert "must be a list" in body.get("error", {}).get("message", "")