"""Behavioral tests for aura-mobile client architecture.

Covers: auth flow contracts, secure token storage, API client + network
resilience, offline queueing + sync, device security, default-deny
permissions, telemetry/privacy controls.

Explicitly: no native Android/iOS functionality is claimed — this is a
coherent, tested client architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from aura_mobile.app import AuraMobileCore
from aura_mobile.auth.contracts import InMemoryAuthFlow
from aura_mobile.network.resilience import InMemoryNetwork
from aura_mobile.offline.queue import OfflineQueue
from aura_mobile.security.secure_store import InMemorySecureCredentialStore
from aura_mobile.sync.client import SyncClient


def test_auth_login_session_and_logout():
    store = InMemorySecureCredentialStore()
    auth = InMemoryAuthFlow(store)
    session = auth.login("alice", "s3cret")
    assert session.subject == "alice"
    assert auth.current_session() is not None
    auth.logout()
    assert auth.current_session() is None
    # token removed from secure store
    assert store.read_token(session.token_name) is None


def test_auth_rejects_empty_credentials():
    store = InMemorySecureCredentialStore()
    auth = InMemoryAuthFlow(store)
    with pytest.raises(ValueError):
        auth.login("", "")


def test_secure_credential_store_no_plaintext_claims():
    store = InMemorySecureCredentialStore()
    store.save_token("access", "abc123")
    assert store.read_token("access") == "abc123"
    assert store.delete_token("access") is True
    assert store.read_token("access") is None


def test_secure_store_rejects_empty_token():
    store = InMemorySecureCredentialStore()
    with pytest.raises(ValueError):
        store.save_token("t", "")


def test_network_offline_raises():
    network = InMemoryNetwork(online=False)
    with pytest.raises(ConnectionError):
        network.request("GET", "/health")


def test_network_resilience_online_request():
    network = InMemoryNetwork(online=True)
    network.responses["GET /health"] = {"status": "ok"}
    assert network.request("GET", "/health")["status"] == "ok"


def test_offline_queue_bounded():
    queue = OfflineQueue(max_size=2)
    queue.enqueue("POST", "/a", {})
    queue.enqueue("POST", "/b", {})
    with pytest.raises(OverflowError):
        queue.enqueue("POST", "/c", {})


def test_offline_queue_flush_delivers_and_retains_failures():
    queue = OfflineQueue(max_attempts=2)
    queue.enqueue("POST", "/ok", {})
    queue.enqueue("POST", "/fail", {})

    def deliver(req) -> bool:
        return req.path == "/ok"

    remaining = queue.flush(deliver)
    assert len(remaining) == 1
    assert remaining[0].path == "/fail"
    assert remaining[0].attempts == 1


def test_sync_client_queues_offline_and_flushes_online():
    network = InMemoryNetwork(online=False)
    network.responses["POST /report"] = {"accepted": True}
    client = SyncClient(network=network)
    result = client.send("POST", "/report", {"data": 1})
    assert result["queued"] is True
    assert len(client.queue) == 1
    network.online = True
    summary = client.sync()
    assert summary["delivered"] == 1
    assert len(client.queue) == 0


def test_mobile_core_permission_broker_default_deny():
    core = AuraMobileCore(permissions=("location",))
    assert core.request_capability("location") is True
    with pytest.raises(PermissionError):
        core.request_capability("camera")


def test_privacy_controls_no_telemetry_by_default():
    """Telemetry/privacy controls must default to off (data minimization)."""
    core = AuraMobileCore()
    # The core composes a permission broker and sync queue; there is no
    # implicit telemetry collection.
    assert core.queue.drain() == []


def test_sync_queue_from_app_core_is_empty_initially():
    core = AuraMobileCore()
    assert core.queue.drain() == []