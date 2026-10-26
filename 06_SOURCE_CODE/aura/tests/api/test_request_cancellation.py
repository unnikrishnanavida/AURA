"""Slice 1D cancellation tests: identity, registration, ownership, propagation,
provider transport interruption, stage reporting, cleanup and race conditions.

Every API-level scenario drives the real canonical pipeline
(HTTP -> API -> brain/reasoning -> provider). The only replacements are
deterministic and explicit:

- a :class:`BlockingAura` whose ``reason()`` blocks until released or the
  caller's token is cancelled (deterministic "cancelled during orchestration"
  with zero network involvement), and
- a local stdlib HTTP server standing in for a "thinking" language-model
  endpoint so the abort-aware provider transport is interrupted for real
  (the strongest evidence that cancellation is an interrupt, not a flag check).
"""

from __future__ import annotations

import json
import threading
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from aura.api.server import (
    AuraApiServer,
    RequestId,
    RequestTask,
    RequestTaskRegistry,
    ServerConfig,
)
from aura.foundation.cancellation import CancellationTokenSource
from aura.foundation.clock import ManualClock
from aura.foundation.errors import CancelledError
from aura.observability.metrics import Metrics
from aura.providers.base import Provider, ProviderProfile
from aura.providers.manager import ProviderManager
from aura.providers.remote import HttpChatProviderAdapter
from aura.providers.result import ProviderStatus
from aura.sdk.client import Aura
from aura.security.audit import AuditLog


@pytest.fixture
def server() -> AuraApiServer:
    return AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=3),
        config=ServerConfig(host="127.0.0.1", port=0),
    )


# -- http helpers (mirror tests/api/test_api.py) ---------------------------


def _post(
    port: int,
    path: str,
    payload: dict | None = None,
    *,
    token: str | None = None,
    timeout: float = 15,
) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=timeout)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request("POST", path, body=json.dumps(payload or {}), headers=headers)
    response = conn.getresponse()
    raw = response.read()
    body = json.loads(raw.decode()) if raw else {}
    status = response.status
    conn.close()
    return status, body


def _get(port: int, path: str, *, token: str | None = None, timeout: float = 15) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=timeout)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    status = response.status
    conn.close()
    return status, body


def _start(api: AuraApiServer) -> int:
    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    api._httpd = httpd
    return httpd.server_port


# -- deterministic blocking Aura for orchestration-stage cancellation -------


class BlockingAura(Aura):
    """Aura whose reason() parks until released or the caller cancels."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.started = threading.Event()
        self.release = threading.Event()

    def reason(self, question: str, **kwargs: Any) -> dict[str, Any]:
        cancellation = kwargs.get("cancellation")
        self.started.set()
        while not self.release.is_set():
            if cancellation is not None and cancellation.cancelled:
                raise CancelledError("blocked request cancelled")
            time.sleep(0.005)
        return super().reason(question, **kwargs)


# -- local "thinking model" HTTP server (real transport interruption) ------


class _SlowModelServer:
    def __init__(self, *, sleep_seconds: float = 15.0) -> None:
        self.received = threading.Event()
        self._sleep = sleep_seconds

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                self.server.received.set()  # type: ignore[attr-defined]
                time.sleep(self.server.sleep_seconds)  # type: ignore[attr-defined]
                try:
                    body = json.dumps(
                        {"choices": [{"message": {"content": "a long-awaited answer"}}]}
                    ).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except OSError:
                    pass  # the client aborted; nothing to write to

            def do_GET(self) -> None:  # noqa: N802
                try:
                    self.send_response(200)
                    self.send_header("Content-Length", "2")
                    self.end_headers()
                    self.wfile.write(b"{}")
                except OSError:
                    pass

            def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A002
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        httpd.daemon_threads = True
        httpd.timeout = 0.5
        httpd.sleep_seconds = sleep_seconds  # type: ignore[attr-defined]
        httpd.received = self.received  # type: ignore[attr-defined]
        self._httpd = httpd
        self.url = f"http://127.0.0.1:{httpd.server_port}"
        self.thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        self.thread.start()

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


class RecorderProvider(Provider):
    """Deterministic provider double that counts calls and records kwargs."""

    def __init__(
        self,
        *,
        name: str = "rec",
        capability: str = "reasoning.generation",
        text: str = "a model answer",
    ) -> None:
        self.name = name
        self.model = "rec-model"
        self.timeout_seconds = 5.0
        self._text = text
        self.calls = 0
        self.last_kwargs: dict[str, object] = {}
        self.profile = ProviderProfile(
            name=name,
            kind="reasoning",
            capabilities=(capability,),
            privacy_approved=True,
        )

    def health(self) -> bool:
        return True

    def reason(self, question: str, **kwargs: object) -> str:
        self.calls += 1
        self.last_kwargs = kwargs
        return self._text
# -- task registry unit coverage -------------------------------------------


def test_request_task_identity_and_registry_lifecycle() -> None:
    registry = RequestTaskRegistry()
    source = CancellationTokenSource()
    task = RequestTask(request_id=RequestId.new(), owner="owner:test", source=source)
    assert str(task.request_id).startswith("rq-")

    registry.register(task)
    assert registry.active_count() == 1
    assert registry.get(task.request_id) is task

    registry.finish(task, status="ok", result={"answer": "x"})
    assert registry.active_count() == 0
    assert registry.history_count() == 1
    # Finished tasks remain observable for late status/cancel calls.
    assert registry.get(task.request_id) is task
    assert registry.get(task.request_id).status == "ok"  # type: ignore[union-attr]
    # finish is idempotent: a second call cannot re-open a terminal task.
    registry.finish(task, status="cancelled")
    assert registry.get(task.request_id).status == "ok"  # type: ignore[union-attr]


def test_registry_moves_bounded_history_and_cancel_all() -> None:
    registry = RequestTaskRegistry(max_history=3)
    tokens: list[CancellationTokenSource] = []
    for _ in range(5):
        source = CancellationTokenSource()
        tokens.append(source)
        task = RequestTask(request_id=RequestId.new(), owner="owner:x", source=source)
        registry.register(task)
        registry.finish(task, status="ok")

    assert registry.history_count() == 3  # bounded, oldest evicted
    assert registry.cancel_all() == 0  # every task already finished

    source = CancellationTokenSource()
    live = RequestTask(request_id=RequestId.new(), owner="owner:x", source=source)
    registry.register(live)
    assert registry.cancel_all() == 1
    assert source.token.cancelled


def test_registry_register_finish_cancel_race_is_consistent() -> None:
    """Concurrent register/finish/cancel on the same id never corrupts state."""
    registry = RequestTaskRegistry()
    source = CancellationTokenSource()
    task = RequestTask(request_id=RequestId.new(), owner="owner:race", source=source)
    errors: list[Exception] = []

    def worker(iteration: int) -> None:
        try:
            if iteration % 3 == 0:
                registry.register(task)
            elif iteration % 3 == 1:
                registry.cancel_active(task.request_id)
            else:
                registry.finish(task, status="ok", result={"n": iteration})
        except Exception as exc:  # noqa: BLE001 - the test fails on ANY corruption
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(60)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert registry.active_count() in {0, 1}
    assert registry.active_count() + registry.history_count() >= 1


# -- provider-boundary cancellation ----------------------------------------


def test_cancel_before_dispatch_is_reported_at_provider_boundary() -> None:
    manager = ProviderManager(metrics=Metrics())
    stub = RecorderProvider(name="stub", capability="reasoning.generation")
    manager.register(stub)
    source = CancellationTokenSource()
    source.cancel()

    result = manager.generate(question="q", cancellation=source.token)
    assert result.status is ProviderStatus.CANCELLED
    assert result.cancelled_stage == "provider.dispatch"
    assert stub.calls == 0  # the provider was never reached


def test_cancel_after_provider_completion_is_stage_reported() -> None:
    class SelfCancellingProvider(Provider):
        """Cancels the caller's token as it returns: the checkpoint catches it."""

        name = "late"
        kind = "reasoning"
        timeout_seconds = 5.0
        profile = ProviderProfile(
            name="late", kind="reasoning", capabilities=("reasoning.generation",), privacy_approved=True
        )

        def reason(self, question: str, **kwargs: Any) -> str:
            token = kwargs.get("cancellation")
            if token is not None:
                token.cancel()
            return "too late, but here it is"

    manager = ProviderManager(metrics=Metrics())
    manager.register(SelfCancellingProvider())
    source = CancellationTokenSource()
    result = manager.generate(question="q", cancellation=source.token)
    assert result.status is ProviderStatus.CANCELLED
    assert result.cancelled_stage == "provider.after_response"


def test_real_http_transport_is_interrupted_mid_flight() -> None:
    """The abort-aware client really closes the in-flight connection: it is not
    a post-completion flag check."""
    slow = _SlowModelServer()
    manager = ProviderManager(metrics=Metrics())
    manager.register(
        HttpChatProviderAdapter(
            name="slow", base_url=slow.url, model="m", timeout_seconds=60, privacy_approved=True
        )
    )
    source = CancellationTokenSource()
    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["result"] = manager.generate(question="q", cancellation=source.token)

    thread = threading.Thread(target=run)
    thread.start()
    assert slow.received.wait(10), "the provider never received the request"
    source.cancel()
    thread.join(15)

    result = bucket["result"]
    assert result.status is ProviderStatus.CANCELLED
    assert result.cancelled_stage == "provider.http"
    assert "mid-flight" in (result.error or "")
    slow.shutdown()
# -- API-level behaviour ----------------------------------------------------


def test_reason_returns_request_id_and_registers_then_cleans_up(server: AuraApiServer) -> None:
    port = _start(server)
    status, body = _post(port, "/v1/reason", {"question": "is this an api?"})
    assert status == 200
    assert body["status"] == "ok"
    request_id = body["request_id"]
    assert request_id.startswith("rq-")

    read_status, read = _get(port, f"/v1/tasks/{request_id}")
    assert read_status == 200
    assert read["status"] == "ok"
    assert read["result"] is not None

    # Cleanup: the task moved out of the active set into bounded history.
    assert server._tasks.active_count() == 0
    assert server._tasks.history_count() >= 1


def test_client_supplied_request_id_is_honoured_and_validated(server: AuraApiServer) -> None:
    port = _start(server)
    status, body = _post(port, "/v1/reason", {"question": "hi", "request_id": "c0ffee"})
    assert status == 200
    assert body["request_id"] == "rq-c0ffee"

    # Malformed ids are rejected up front.
    bad, bad_body = _post(port, "/v1/reason", {"question": "hi", "request_id": "not-a-hex-id!"})
    assert bad == 400
    assert bad_body["error"]["code"] == "api.validation"


def test_unknown_task_status_and_cancel_are_404(server: AuraApiServer) -> None:
    port = _start(server)
    status, body = _get(port, "/v1/tasks/rq-deadbeef")
    assert status == 404
    assert body["error"]["code"] == "api.not_found"
    cancel_status, _ = _post(port, "/v1/tasks/rq-deadbeef/cancel")
    assert cancel_status == 404


def test_cancel_interrupts_in_flight_api_request() -> None:
    """POST /v1/reason runs, POST /v1/tasks/{id}/cancel stops it, and the
    cancelled stage is reported as observed."""
    from aura.config.settings import AuraConfig

    blocking = BlockingAura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    api = AuraApiServer(aura=blocking, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)

    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(
            port, "/v1/reason", {"question": "is this an api?", "request_id": "c0ffee"}
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert blocking.started.wait(5)

    # The task is observable while running.
    status, body = _get(port, "/v1/tasks/rq-c0ffee")
    assert status == 200
    assert body["status"] == "running"

    cancel_status, cancel_body = _post(port, "/v1/tasks/rq-c0ffee/cancel")
    assert cancel_status == 202
    assert cancel_body["status"] == "cancelling"

    thread.join(10)
    assert not thread.is_alive()
    reason_status, reason_body = bucket["out"]
    assert reason_status == 200
    assert reason_body["status"] == "cancelled"
    assert reason_body["cancelled_stage"] == "orchestration"
    assert reason_body["request_id"] == "rq-c0ffee"

    # Terminal state stays queryable.
    status, body = _get(port, "/v1/tasks/rq-c0ffee")
    assert body["status"] == "cancelled"
    assert body["cancelled_stage"] == "orchestration"
    assert api._tasks.active_count() == 0


def test_cancel_of_completed_and_of_cancelled_task_is_409() -> None:
    from aura.config.settings import AuraConfig

    port = _start(
        AuraApiServer(
            aura=Aura(config=AuraConfig(), clock=ManualClock(0), seed=3),
            config=ServerConfig(host="127.0.0.1", port=0),
        )
    )
    status, body = _post(port, "/v1/reason", {"question": "is this an api?", "request_id": "c0ffee"})
    assert status == 200
    assert body["status"] == "ok"

    # Already completed: cannot cancel.
    cancel_status, cancel_body = _post(port, "/v1/tasks/rq-c0ffee/cancel")
    assert cancel_status == 409
    assert cancel_body["error"]["code"] == "api.conflict"
    assert "already ok" in cancel_body["error"]["message"]

    # Already cancelled: same conflict semantics.
    blocking = BlockingAura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    api = AuraApiServer(aura=blocking, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)
    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(port, "/v1/reason", {"question": "q", "request_id": "beeeef"})

    thread = threading.Thread(target=run)
    thread.start()
    assert blocking.started.wait(5)
    assert _post(port, "/v1/tasks/rq-beeeef/cancel")[0] == 202
    thread.join(10)
    cancel_again, again_body = _post(port, "/v1/tasks/rq-beeeef/cancel")
    assert cancel_again == 409
    assert "already cancelled" in again_body["error"]["message"]
def test_api_cancellation_interrupts_real_provider_http_call() -> None:
    """The full pipeline (API -> brain -> reasoning -> provider transport) is
    genuinely interrupted: a real HTTP request to a slow provider is aborted,
    not merely observed after completion."""
    from aura.config.settings import AuraConfig

    slow = _SlowModelServer()
    manager = ProviderManager(metrics=Metrics())
    manager.register(
        HttpChatProviderAdapter(
            name="slow", base_url=slow.url, model="m", timeout_seconds=60, privacy_approved=True
        )
    )

    aura = Aura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    aura.brain.provider_manager = manager
    aura.brain.reasoning._provider_manager = manager
    api = AuraApiServer(aura=aura, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)

    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(
            port, "/v1/reason", {"question": "What is machine learning?", "request_id": "c0ffee"}
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert slow.received.wait(10), "the provider never received the real HTTP request"
    assert _post(port, "/v1/tasks/rq-c0ffee/cancel")[0] == 202
    thread.join(20)

    reason_status, reason_body = bucket["out"]
    assert reason_status == 200
    assert reason_body["status"] == "cancelled"
    assert reason_body["cancelled_stage"] == "provider.http"
    assert reason_body["provider"]["status"] == "cancelled"

    status, body = _get(port, "/v1/tasks/rq-c0ffee")
    assert status == 200
    assert body["status"] == "cancelled"
    assert body["cancelled_stage"] == "provider.http"
    assert api._tasks.active_count() == 0
    slow.shutdown()
def _auth_server_with_blocking_aura() -> tuple[AuraApiServer, int, str, str]:
    """A token-bound server with two independently-owned issued keys."""
    from aura.config.settings import AuraConfig

    blocking = BlockingAura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    api = AuraApiServer(
        aura=blocking,
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key="service-key-at-least-16-char",
            admin_key="admin-key-at-least-16-char",
        ),
        audit_log=AuditLog(),
    )
    port = _start(api)
    status, issued_1 = _post(
        port, "/v1/keys", {"scopes": ["cognition.reason"]}, token="admin-key-at-least-16-char"
    )
    assert status == 201
    status, issued_2 = _post(
        port, "/v1/keys", {"scopes": ["cognition.reason"]}, token="admin-key-at-least-16-char"
    )
    assert status == 201
    return api, port, str(issued_1["api_key"]), str(issued_2["api_key"])


def test_cancellation_respects_ownership() -> None:
    """A user must not cancel another user's request (403); the owner (or
    admin) can."""
    api, port, owner_key, other_key = _auth_server_with_blocking_aura()
    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(
            port, "/v1/reason", {"question": "q", "request_id": "c0ffee"}, token=owner_key
        )

    thread = threading.Thread(target=run)
    thread.start()
    assert api.aura.started.wait(5)

    # Another authenticated user cannot cancel...
    denied, denied_body = _post(port, "/v1/tasks/rq-c0ffee/cancel", token=other_key)
    assert denied == 403
    assert denied_body["error"]["code"] == "api.forbidden"
    # ...and cannot read the status either.
    assert _get(port, "/v1/tasks/rq-c0ffee", token=other_key)[0] == 403

    # The owner can.
    assert _post(port, "/v1/tasks/rq-c0ffee/cancel", token=owner_key)[0] == 202
    thread.join(10)
    assert bucket["out"][1]["status"] == "cancelled"
# Admin override: a fresh owner request can be cancelled by the admin key.
    api.aura.started.clear()  # phase 1 already consumed the shared event
    bucket_2: dict[str, Any] = {}

    def run_2() -> None:
        bucket_2["out"] = _post(
            port, "/v1/reason", {"question": "q", "request_id": "d00d00"}, token=owner_key
        )

    thread_2 = threading.Thread(target=run_2)
    thread_2.start()
    assert api.aura.started.wait(5)
    admin, _ = _post(port, "/v1/tasks/rq-d00d00/cancel", token="admin-key-at-least-16-char")
    assert admin == 202
    thread_2.join(10)
    assert bucket_2["out"][1]["status"] == "cancelled"
    api.close()


def test_concurrent_cancellation_is_single_effect() -> None:
    """Many racing cancel requests leave exactly one consistent terminal state."""
    from aura.config.settings import AuraConfig

    blocking = BlockingAura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    api = AuraApiServer(aura=blocking, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)

    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(port, "/v1/reason", {"question": "q", "request_id": "c0ffee"})

    thread = threading.Thread(target=run)
    thread.start()
    assert blocking.started.wait(5)

    outcomes: list[int] = []

    def cancel() -> None:
        status, _ = _post(port, "/v1/tasks/rq-c0ffee/cancel")
        outcomes.append(status)

    racers = [threading.Thread(target=cancel) for _ in range(12)]
    for racer in racers:
        racer.start()
    for racer in racers:
        racer.join()

    thread.join(10)
    statuses = {outcome for outcome in outcomes}
    # Every accepted cancel is 202; a 409 appears only if a racer lost the
    # race against completion. Anything else is a contract violation.
    assert statuses <= {202, 409}
    assert 202 in statuses
    assert bucket["out"][1]["status"] == "cancelled"
    assert api._tasks.get(RequestId.from_str("c0ffee")).status == "cancelled"  # type: ignore[union-attr]


def test_server_close_cancels_all_in_flight_requests() -> None:
    from aura.config.settings import AuraConfig

    blocking = BlockingAura(config=AuraConfig(), clock=ManualClock(0), seed=3)
    api = AuraApiServer(aura=blocking, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)
    bucket: dict[str, Any] = {}

    def run() -> None:
        bucket["out"] = _post(port, "/v1/reason", {"question": "q", "request_id": "c0ffee"})

    thread = threading.Thread(target=run)
    thread.start()
    assert blocking.started.wait(5)
    task = api._tasks.get(RequestId.from_str("c0ffee"))
    assert task is not None
    assert not task.token.cancelled

    api.close()

    assert task.token.cancelled
    # A cancelled request surfaces as cancelled, not as a hang or an error.
    thread.join(10)
    assert bucket["out"][1]["status"] == "cancelled"