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
def test_server_close_releases_memory_store() -> None:
    """AuraApiServer.close() deterministically closes the memory store (P28-1)."""
    closed: list[str] = []

    class _Store:
        def close(self) -> None:
            closed.append("closed")

    class _Memory:
        def __init__(self) -> None:
            self.store = _Store()

    class _Brain:
        def __init__(self) -> None:
            self.memory = _Memory()

    class _Aura:
        def __init__(self) -> None:
            self.brain = _Brain()

    api = AuraApiServer(aura=_Aura(), config=ServerConfig(host="127.0.0.1", port=0))
    assert closed == []
    api.close()
    assert closed == ["closed"]
    api.close()  # must not raise when called again
    assert closed == ["closed", "closed"]


def test_server_close_skips_store_without_close() -> None:
    """Stores without a close() (e.g. in-memory) are skipped, never an error."""

    class _Brain:
        def __init__(self) -> None:
            self.memory = type("_Memory", (), {"store": object()})()

    class _Aura:
        def __init__(self) -> None:
            self.brain = _Brain()

    api = AuraApiServer(aura=_Aura(), config=ServerConfig(host="127.0.0.1", port=0))
    api.close()
    api.close()


def test_server_close_closes_distributed_state_pool() -> None:
    """The distributed-state connection pool is released on close (P28-3)."""
    pool_closed: list[str] = []

    class _Pool:
        def close(self) -> None:
            pool_closed.append("pool-closed")

    api = AuraApiServer(aura=object(), config=ServerConfig(host="127.0.0.1", port=0))
    api._distributed_state = _Pool()
    assert pool_closed == []
    api.close()
    assert pool_closed == ["pool-closed"]
    api.close()
    assert pool_closed == ["pool-closed", "pool-closed"]


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


def test_sqlite_backed_api_persists_across_server_restart(tmp_path: object) -> None:
    """A memory written through the API survives a full server-round restart."""
    from pathlib import Path

    from aura.config.settings import AuraConfig, Environments, StorageConfig
    from aura.foundation.clock import ManualClock

    db_path = Path(tmp_path) / "api.sqlite3"  # type: ignore[arg-type]
    cfg = AuraConfig(
        storage=StorageConfig(backend="sqlite", sqlite_path=str(db_path)),
        environment=Environments.DEV,
    )
    server_one = AuraApiServer(
        aura=Aura(clock=ManualClock(0), config=cfg),
        config=ServerConfig(host="127.0.0.1", port=0),
    )
    port_one = _start(server_one)
    status, body = _post(port_one, "/v1/remember", {"key": "persistent", "content": {"v": 7}})
    assert status == 200
    memory_id = body["memory_id"]
    assert memory_id
    server_one._httpd.shutdown()  # type: ignore[attr-defined]
    server_one._httpd.server_close()  # type: ignore[attr-defined]
    server_one.aura.brain.memory.store.close()  # type: ignore[attr-defined]

    # Simulate process restart: a brand-new server over the same file.
    server_two = AuraApiServer(
        aura=Aura(clock=ManualClock(0), config=cfg),
        config=ServerConfig(host="127.0.0.1", port=0),
    )
    port_two = _start(server_two)
    status, body = _post(port_two, "/v1/recall", {"text": "persistent", "limit": 10})
    assert status == 200
    assert any(entry["key"] == "persistent" for entry in body["entries"])


def test_api_with_sqlite_migrations_on_open() -> None:
    """AuraApiServer with an sqlite-backed Aura applies migrations at startup."""
    import tempfile

    from aura.config.settings import AuraConfig, StorageConfig

    tmp = tempfile.mkdtemp()
    db_file = f"{tmp}/mig.sqlite3"
    cfg = AuraConfig(storage=StorageConfig(backend="sqlite", sqlite_path=db_file))
    api = AuraApiServer(aura=Aura(config=cfg))
    health = api.aura.health()
    assert health["status"] == "ok"
    assert "SQLiteMemoryStore" in str(health["engines"]["memory"]["backend"])
    # close the underlying file to release the lock
    store = api.aura.brain.memory.store
    store.close()  # type: ignore[attr-defined]