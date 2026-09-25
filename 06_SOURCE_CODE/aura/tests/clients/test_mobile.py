"""Phase 34 mobile tests: offline-first queue, snapshot, reconnect sync, auth storage."""

from __future__ import annotations

import tempfile

from aura.clients.mobile import MobileClient, SyncSnapshot
from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import MemorySecureStore


class FakeApi:
    def __init__(self) -> None:
        self.healthy = True
        self.calls: list[str] = []

    def ready(self) -> bool:
        return self.healthy

    def reason(self, question: str, facts: object = None) -> dict[str, object]:
        self.calls.append(question)
        return {"answer": "ok", "question": question}


def _client() -> tuple[MobileClient, FakeApi, OfflineQueue]:
    api = FakeApi()
    queue = OfflineQueue(tempfile.mkdtemp())
    client = MobileClient(api=api, storage=MemorySecureStore(), queue=queue, platform="android")
    return client, api, queue


def test_online_path() -> None:
    client, api, _ = _client()
    result = client.reason("hi")
    assert result["answer"] == "ok"
    assert client.snapshot() == SyncSnapshot(pending=0, last_sequence=-1)


def test_offline_queues_and_syncs_on_reconnect() -> None:
    client, api, queue = _client()
    api.healthy = False
    queued = client.reason("offline q")
    assert queued.get("queued") is True
    queued2 = client.reason("offline q")  # duplicate idempotency key
    assert queued2 is not None
    assert queue.count() == 1  # deduplicated
    snapshot = client.snapshot()
    assert snapshot.pending == 1
    assert snapshot.conflict_strategy == "last-write-wins"

    api.healthy = True
    counts = client.sync()
    assert counts == {"replayed": 1, "failed": 0, "remaining": 0}
    assert api.calls == ["offline q"]


def test_auth_secure_storage() -> None:
    client, _, _ = _client()
    assert client.auth_saved() is False
    client.save_auth("mob-key")
    assert client.auth_saved() is True
    client.clear_auth()
    assert client.auth_saved() is False


def test_snapshot_to_dict() -> None:
    snapshot = SyncSnapshot(pending=3, last_sequence=2)
    data = snapshot.to_dict()
    assert data["pending"] == 3 and data["conflict_strategy"] == "last-write-wins"