"""Tests for GET /v1/research/runs: owner isolation, bounds, ordering, pagination."""

from __future__ import annotations

import hashlib
import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.foundation.ids import CorrelationId, ExecutionId
from aura.sdk.client import Aura


@pytest.fixture
def server() -> AuraApiServer:
    aura = Aura(clock=ManualClock(0), seed=3)
    return AuraApiServer(aura=aura, config=ServerConfig(host="127.0.0.1", port=0))


@pytest.fixture
def secured_server() -> AuraApiServer:
    aura = Aura(clock=ManualClock(0), seed=4)
    return AuraApiServer(aura=aura, config=ServerConfig(host="127.0.0.1", port=0, api_key="sekret"))


def _start(api: AuraApiServer) -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    api._httpd = httpd
    return httpd.server_port


def _request(
    port: int, method: str, path: str, *, token: str | None = None, body: dict | None = None
) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    headers: dict[str, str] = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        conn.request(method, path, body=json.dumps(body), headers=headers)
    else:
        conn.request(method, path, headers=headers)
    response = conn.getresponse()
    payload = json.loads(response.read().decode())
    conn.close()
    return response.status, payload


def _get(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    return _request(port, "GET", path, token=token)


def _post(port: int, path: str, body: dict, *, token: str | None = None) -> tuple[int, dict]:
    return _request(port, "POST", path, token=token, body=body)


def _run(port: int, question: str, *, token: str | None = None) -> None:
    status, _ = _post(port, "/v1/research", {"question": question}, token=token)
    assert status == 200


def test_authenticated_success_and_real_fields(server: AuraApiServer) -> None:
    port = _start(server)
    _, output = _post(port, "/v1/research", {"question": "is the sky blue?"}, token="tok-a")
    run_id = output["execution_id"]

    status, payload = _get(port, "/v1/research/runs", token="tok-a")
    assert status == 200
    assert payload["count"] == 1
    assert payload["next_cursor"] is None
    run = payload["runs"][0]
    assert run["run_id"] == run_id
    assert run["status"] == "completed"
    assert run["question"] == "is the sky blue?"
    assert isinstance(run["findings_count"], int)
    assert run["epistemic"] in {"evidence", "inference", "hypothesis", "speculation", "unknown"}
    assert run["started_at"]


def test_unauthenticated_request_is_rejected(secured_server: AuraApiServer) -> None:
    port = _start(secured_server)
    status, payload = _get(port, "/v1/research/runs")
    assert status == 401
    assert payload["error"]["code"] == "api.auth_failed"

    status, _ = _post(port, "/v1/research", {"question": "q"}, token="sekret")
    assert status == 200


def test_invalid_and_out_of_range_limits_and_cursors(server: AuraApiServer) -> None:
    port = _start(server)
    for bad in ("0", "-1", "51", "abc"):
        status, payload = _get(port, f"/v1/research/runs?limit={bad}", token="tok-a")
        assert status == 400, bad
        assert payload["error"]["code"] == "api.validation"
    for bad_cursor in ("abc", "0", "-4"):
        status, payload = _get(port, f"/v1/research/runs?cursor={bad_cursor}", token="tok-a")
        assert status == 400, bad_cursor
        assert payload["error"]["code"] == "api.validation"


def test_empty_result_is_a_valid_empty_collection(server: AuraApiServer) -> None:
    port = _start(server)
    status, payload = _get(port, "/v1/research/runs", token="tok-a")
    assert status == 200
    assert payload == {"runs": [], "next_cursor": None, "count": 0, "limit": 20}


def test_deterministic_newest_first_ordering(server: AuraApiServer) -> None:
    port = _start(server)
    _run(port, "first question", token="tok-a")
    _run(port, "second question", token="tok-a")
    first = _get(port, "/v1/research/runs", token="tok-a")
    second = _get(port, "/v1/research/runs", token="tok-a")
    assert first == second
    assert [r["question"] for r in first[1]["runs"]] == ["second question", "first question"]


def test_owner_isolation_across_two_users(server: AuraApiServer) -> None:
    port = _start(server)
    _run(port, "secret for alice only", token="tok-alice")
    _run(port, "secret for bob only", token="tok-bob")

    _, alice = _get(port, "/v1/research/runs", token="tok-alice")
    _, bob = _get(port, "/v1/research/runs", token="tok-bob")
    _, anon = _get(port, "/v1/research/runs")
    assert [r["question"] for r in alice["runs"]] == ["secret for alice only"]
    assert [r["question"] for r in bob["runs"]] == ["secret for bob only"]
    assert anon["runs"] == []


def test_legacy_unscoped_events_are_anonymous_only(server: AuraApiServer) -> None:
    """Events recorded before scope attribution default to the anonymous owner."""
    port = _start(server)
    server.aura.brain.recorder.record(
        event_type="research.completed",
        source="aura.sdk.research",
        execution_id=ExecutionId.new(),
        correlation_id=CorrelationId.new(),
        payload={"question": "legacy question", "findings": 0, "epistemic": "unknown"},
    )
    _, anon = _get(port, "/v1/research/runs")
    _, owner = _get(port, "/v1/research/runs", token="tok-a")
    assert [r["question"] for r in anon["runs"]] == ["legacy question"]
    assert owner["runs"] == []


def test_cursor_pagination_is_deterministic_and_non_overlapping(server: AuraApiServer) -> None:
    port = _start(server)
    for i in range(3):
        _run(port, f"question {i}", token="tok-a")

    status1, page1 = _get(port, "/v1/research/runs?limit=2", token="tok-a")
    assert status1 == 200
    assert [r["question"] for r in page1["runs"]] == ["question 2", "question 1"]
    assert isinstance(page1["next_cursor"], int)
    cursor: int = page1["next_cursor"]  # type: ignore[assignment]

    status2, page2 = _get(port, f"/v1/research/runs?limit=2&cursor={cursor}", token="tok-a")
    assert status2 == 200
    assert [r["question"] for r in page2["runs"]] == ["question 0"]
    assert page2["next_cursor"] is None

    seen = [r["run_id"] for r in page1["runs"]] + [r["run_id"] for r in page2["runs"]]
    assert len(seen) == len(set(seen))

    status3, page3 = _get(port, f"/v1/research/runs?limit=2&cursor={cursor}", token="tok-a")
    assert status3 == 200
    assert page3["runs"] == page2["runs"]

    status4, page4 = _get(port, "/v1/research/runs?limit=2&cursor=1", token="tok-a")
    assert status4 == 200
    assert page4["runs"] == []
    assert page4["next_cursor"] is None


def test_safe_response_fields_only(server: AuraApiServer) -> None:
    port = _start(server)
    _run(port, "safe fields question", token="tok-a")
    _, payload = _get(port, "/v1/research/runs", token="tok-a")
    run = payload["runs"][0]
    assert set(run) == {"run_id", "status", "question", "findings_count", "epistemic", "started_at"}
    assert set(payload) == {"runs", "next_cursor", "count", "limit"}
    serialized = json.dumps(run).lower()
    for leaked in ("authorization", "secret", "password", "token", "scope", "payload"):
        assert leaked not in serialized


def test_research_post_still_records_a_run(server: AuraApiServer) -> None:
    port = _start(server)
    status, output = _post(
        port,
        "/v1/research",
        {"question": "regression", "claims": ["claim alpha", "claim beta"]},
        token="tok-a",
    )
    assert status == 200
    assert len(output["findings"]) == 2
    events = server.aura.brain.recorder.events(event_type="research.completed")
    assert len(events) == 1
    assert events[0].payload["question"] == "regression"
    assert events[0].payload["scope"] == "owner:" + hashlib.sha256(b"tok-a").hexdigest()[:16]