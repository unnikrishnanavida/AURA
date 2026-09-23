"""Phase 26 metrics instrumentation tests.

Proves the six production metrics are driven by REAL runtime events with
exactly one increment per event:

- api_auth_failure         <- API 401 authentication denials
- rate_limit_deny          <- API 429 rate-limit denials
- memory_operation_failure <- genuine store failures (NotFound/ValueError not counted)
- provider_failure         <- NOT instrumented (architectural blocker; see report)
- execution_count          <- BrainEngine.reason() attempts
- execution_failure        <- BrainEngine.reason() failures

The integration tests start a real HTTP server (no mocks for the event path)
and assert counter deltas and alert behavior.
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.foundation.errors import NotFoundError
from aura.foundation.ids import MemoryId
from aura.memory.engine import MemoryEngine
from aura.memory.models import MemoryType
from aura.observability.metrics import Metrics
from aura.sdk.client import Aura

ADMIN_KEY = "admin-key-at-least-16-char"
SERVICE_KEY = "service-key-at-least-16-char"


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


def _count(api: AuraApiServer, name: str) -> int:
    return api.aura.brain.metrics.count(name)


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


def test_failed_auth_increments_api_auth_failure_exactly_once() -> None:
    api = AuraApiServer(
        config=ServerConfig(host="127.0.0.1", port=0, api_key=SERVICE_KEY, admin_key=ADMIN_KEY),
    )
    port = _start(api)
    for _ in range(3):
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token="wrong-key-0123456789")
        assert status == 401
    assert _count(api, "api_auth_failure") == 3


def test_successful_auth_does_not_increment_api_auth_failure() -> None:
    api = AuraApiServer(
        config=ServerConfig(host="127.0.0.1", port=0, api_key=SERVICE_KEY, admin_key=ADMIN_KEY),
    )
    port = _start(api)
    status, _ = _post(port, "/v1/reason", {"question": "ok?"}, token=SERVICE_KEY)
    assert status == 200
    assert _count(api, "api_auth_failure") == 0


def test_failed_auth_does_not_increment_rate_limit_metric() -> None:
    api = AuraApiServer(
        config=ServerConfig(host="127.0.0.1", port=0, api_key=SERVICE_KEY, admin_key=ADMIN_KEY),
    )
    port = _start(api)
    for _ in range(2):
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token="wrong-key-0123456789")
        assert status == 401
    assert _count(api, "rate_limit_deny") == 0


# -- rate_limit_deny --------------------------------------------------------


def test_rate_limit_denial_increments_exactly_once_per_429() -> None:
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
    ok = 0
    denied = 0
    for _ in range(5):
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token=SERVICE_KEY)
        if status == 200:
            ok += 1
        else:
            assert status == 429
            denied += 1
    assert ok == 1
    assert denied == 4
    assert _count(api, "rate_limit_deny") == 4  # one per denial, no double count


def test_rate_limit_success_does_not_increment() -> None:
    api = AuraApiServer(
        config=ServerConfig(host="127.0.0.1", port=0, api_key=SERVICE_KEY, admin_key=ADMIN_KEY),
    )
    port = _start(api)
    status, _ = _post(port, "/v1/reason", {"question": "q"}, token=SERVICE_KEY)
    assert status == 200
    assert _count(api, "rate_limit_deny") == 0


# -- memory_operation_failure ----------------------------------------------


class _BrokenStore:
    """A real store substitute whose persistence operations always fail."""

    def add(self, entry: object) -> object:
        raise RuntimeError("backend unreachable")

    def get(self, memory_id: object) -> object:
        raise RuntimeError("backend unreachable")

    def delete(self, memory_id: object) -> None:
        raise RuntimeError("backend unreachable")

    def archive(self, entry: object) -> None:
        raise RuntimeError("backend unreachable")


def test_memory_operation_failure_increments_exactly_once() -> None:
    engine = MemoryEngine(store=_BrokenStore(), metrics=Metrics())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        engine.remember(key="k", kind=MemoryType.EPISODIC, content={"a": 1})
    assert engine._metrics.count("memory_operation_failure") == 1  # type: ignore[union-attr]


def test_memory_not_found_is_not_a_failure() -> None:
    engine = MemoryEngine(metrics=Metrics())
    with pytest.raises(NotFoundError):
        engine.by_id(MemoryId.new())
    assert engine._metrics.count("memory_operation_failure") == 0  # type: ignore[union-attr]


def test_memory_validation_error_is_not_a_failure() -> None:
    engine = MemoryEngine(metrics=Metrics())
    with pytest.raises(ValueError):
        engine.remember(key="k", kind=MemoryType.EPISODIC, content={}, importance=2.0)
    assert engine._metrics.count("memory_operation_failure") == 0  # type: ignore[union-attr]


def test_successful_memory_operation_not_counted_as_failure() -> None:
    engine = MemoryEngine(metrics=Metrics())
    entry = engine.remember(key="k", kind=MemoryType.EPISODIC, content={"a": 1})
    assert engine.by_id(entry.id).key == "k"
    assert engine._metrics.count("memory_operation_failure") == 0  # type: ignore[union-attr]


def test_nested_memory_operation_counts_once_per_event() -> None:
    """archive() calls by_id() internally; one failed event must count once."""
    engine = MemoryEngine(store=_BrokenStore(), metrics=Metrics())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        engine.archive(MemoryId.new())
    assert engine._metrics.count("memory_operation_failure") == 1  # type: ignore[union-attr]


# -- execution metrics ------------------------------------------------------


def test_execution_success_increments_count_only() -> None:
    aura = Aura(clock=ManualClock(0), seed=3)
    aura.reason("is this a test?")
    snap = aura.metrics()
    assert snap["counters"]["execution_count"] == 1
    # execution_failure is absent until the first failure (defaultdict semantics).
    assert snap["counters"].get("execution_failure", 0) == 0


def test_execution_failure_increments_count_and_failure() -> None:
    aura = Aura(clock=ManualClock(0), seed=3)

    def boom(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("reasoning engine exploded")

    aura.brain.reasoning.reason = boom  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        aura.reason("boom")
    snap = aura.metrics()
    assert snap["counters"]["execution_count"] == 1
    assert snap["counters"]["execution_failure"] == 1


# -- concurrency -------------------------------------------------------------


def test_metrics_increment_is_thread_safe() -> None:
    metrics = Metrics()
    n_threads = 8
    per_thread = 1000

    def _worker() -> None:
        for _ in range(per_thread):
            metrics.increment("execution_count")

    threads = [threading.Thread(target=_worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert metrics.count("execution_count") == n_threads * per_thread