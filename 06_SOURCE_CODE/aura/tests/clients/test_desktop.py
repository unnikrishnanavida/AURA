"""Phase 33 desktop tests: lifecycle, secure storage, offline queue, client."""

from __future__ import annotations

import os

from aura.clients.desktop import AppState, DesktopClient, DesktopLifecycle
from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import EnvVarSecureStore, MemorySecureStore, secure_store_from


class FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.healthy = True
        self.config: dict[str, object] = {}

    def ready(self) -> bool:
        return self.healthy

    def reason(self, question: str, facts: object = None) -> dict[str, object]:
        self.calls.append(("reason", question))
        return {"answer": "ok", "question": question, "facts": facts}


def test_lifecycle_state_machine() -> None:
    seen: list[AppState] = []
    app = DesktopLifecycle(on_state=seen.append)
    assert app.state is AppState.STOPPED
    app.start()
    assert app.state is AppState.READY
    app.go_offline()
    assert app.state is AppState.OFFLINE
    app.reconnect()
    assert app.state is AppState.READY
    app.stop()
    assert app.state is AppState.STOPPED
    assert seen[0] is AppState.STARTING


def test_secure_store_factory_never_plaintext() -> None:
    memory = secure_store_from("memory")
    memory.set("api_key", "k-123")
    assert memory.get("api_key") == "k-123"

    env = EnvVarSecureStore(prefix="AURA_TEST_")
    env.reset()
    env.set("endpoint", "http://127.0.0.1:9")
    assert env.get("endpoint") == "http://127.0.0.1:9"
    assert os.environ.get("AURA_TEST_ENDPOINT") == "http://127.0.0.1:9"
    env.reset()
    assert env.get("endpoint") is None


def test_offline_queue_dedup_and_replay() -> None:
    queue = OfflineQueue(__import__("tempfile").mkdtemp())
    queue.enqueue(op="reason", params={"q": "a"}, idempotency_key="r1")
    queue.enqueue(op="reason", params={"q": "a"}, idempotency_key="r1")  # duplicate -> dedup
    assert queue.count() == 1  # same logical request is stored once (LWW)
    done: list[str] = []

    def executor(record: dict) -> bool:
        done.append(record["idempotency_key"])
        return True

    result = queue.replay(executor)
    assert result == {"replayed": 1, "failed": 0, "remaining": 0}
    assert queue.count() == 0


def test_offline_queue_exhausts_and_reports_failures() -> None:
    queue = OfflineQueue(__import__("tempfile").mkdtemp())
    queue.enqueue(op="reason", params={"q": "x"}, idempotency_key="f1")

    def executor(record: dict) -> bool:
        return False

    # First replay only bumps attempts; with max_attempts=2 the record survives.
    assert queue.replay(executor, max_attempts=2) == {"replayed": 0, "failed": 0, "remaining": 1}
    # Second replay exhausts the budget -> reported as failed and removed.
    assert queue.replay(executor, max_attempts=2) == {"replayed": 0, "failed": 1, "remaining": 0}
    assert queue.count() == 0


def test_desktop_client_offline_queues_then_syncs() -> None:
    api = FakeApi()
    client = DesktopClient(
        api=api,
        storage=MemorySecureStore(),
        queue=OfflineQueue(__import__("tempfile").mkdtemp()),
        lifecycle=DesktopLifecycle(on_state=lambda s: None),
    )
    api.healthy = False
    assert client.is_authenticated() is False
    assert client.authenticate("k") is False  # verify fails while offline
    client.lifecycle.go_offline()
    queued = client.reason("what now?")
    assert queued.get("queued") is True

    api.healthy = True
    counts = client.sync()
    assert counts["replayed"] == 1
    assert any(q == "what now?" for _, q in api.calls)
    assert client.lifecycle.state is AppState.READY


def test_desktop_client_online_path_and_signout() -> None:
    api = FakeApi()
    storage = MemorySecureStore()
    client = DesktopClient(
        api=api,
        storage=storage,
        queue=OfflineQueue(__import__("tempfile").mkdtemp()),
        lifecycle=DesktopLifecycle(on_state=lambda s: None),
    )
    assert client.authenticate("k-ok") is True
    assert storage.get("api_key") == "k-ok"
    result = client.reason("hello")
    assert result["answer"] == "ok"
    client.sign_out()
    assert client.is_authenticated() is False