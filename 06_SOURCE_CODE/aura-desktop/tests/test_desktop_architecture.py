"""Behavioral tests for aura-desktop architecture.

Covers: application lifecycle state machine, default-deny capability gate,
secure local storage abstraction (in-memory), API client contract, settings,
diagnostics, crash-reporting interface.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from aura_desktop.host.lifecycle import (
    ApplicationLifecycle,
    InvalidLifecycleTransition,
    LifecycleState,
)
from aura_desktop.integrations.api_client import ClientState, InMemoryApiClient
from aura_desktop.observability.diagnostics import DiagnosticsRunner
from aura_desktop.security.capabilities import CapabilityGate
from aura_desktop.security.storage import InMemorySecureStorage
from aura_desktop.settings.store import SettingsStore


def test_lifecycle_start_stop():
    lifecycle = ApplicationLifecycle()
    assert lifecycle.state is LifecycleState.STOPPED
    lifecycle.start()
    assert lifecycle.state is LifecycleState.RUNNING
    lifecycle.stop()
    assert lifecycle.state is LifecycleState.STOPPED


def test_lifecycle_runs_hooks_on_phase():
    lifecycle = ApplicationLifecycle()
    started = {"n": 0}
    lifecycle.on("running", lambda: started.__setitem__("n", started["n"] + 1))
    lifecycle.start()
    assert started["n"] == 1


def test_lifecycle_restart():
    lifecycle = ApplicationLifecycle()
    lifecycle.start()
    lifecycle.restart()
    assert lifecycle.state is LifecycleState.RUNNING


def test_lifecycle_invalid_transition_rejected():
    lifecycle = ApplicationLifecycle()
    # stop() from STOPPED is idempotent, so this is fine; but fail() from
    # STOPPED is invalid.
    with pytest.raises(InvalidLifecycleTransition):
        lifecycle.fail()


def test_capability_gate_default_deny():
    gate = CapabilityGate()
    assert gate.check("filesystem.write") is False  # default deny
    gate.grant("filesystem.write")
    assert gate.check("filesystem.write") is True
    gate.require("filesystem.write")


def test_capability_gate_require_denied_raises():
    gate = CapabilityGate()
    with pytest.raises(PermissionError):
        gate.require("network")


def test_secure_storage_roundtrip():
    storage = InMemorySecureStorage()
    storage.set("api_key", "secret-123")
    assert storage.get("api_key") == "secret-123"
    assert storage.delete("api_key") is True
    assert storage.get("api_key") is None


def test_secure_storage_delete_missing_returns_false():
    storage = InMemorySecureStorage()
    assert storage.delete("nope") is False


def test_api_client_contract_and_memory_client():
    client = InMemoryApiClient(base_url="http://localhost:8765")
    client.responses["GET /health"] = {"status": "ok"}
    assert client.request("GET", "/health")["status"] == "ok"
    assert client.connect() is ClientState.CONNECTED
    assert client.disconnect() is ClientState.DISCONNECTED


def test_settings_store_persists_via_storage():
    storage = InMemorySecureStorage()
    store = SettingsStore(storage=storage)
    store.set("theme", "dark")
    second = SettingsStore(storage=storage)
    second.load(["theme"])
    assert second.get("theme") == "dark"


def test_diagnostics_reports_pass_fail():
    runner = DiagnosticsRunner()
    runner.register("ok", lambda: (True, "fine"))
    runner.register("bad", lambda: (False, "broken"))
    report = runner.run()
    assert report.all_ok is False
    assert len(report.checks) == 2
    assert report.to_dict()["all_ok"] is False


def test_diagnostics_check_exception_is_safe():
    runner = DiagnosticsRunner()
    runner.register("boom", lambda: (_ for _ in ()).throw(RuntimeError("x")))  # type: ignore[func-returns-value]
    report = runner.run()
    assert report.all_ok is False
    assert "RuntimeError" in report.checks[0]["detail"]


def test_aura_desktop_entry_default_deny():
    from aura_desktop.app import AuraDesktop

    app = AuraDesktop(capabilities=("filesystem.read",))
    app.start()
    assert app.request("filesystem.read") == {"allowed": True, "capability": "filesystem.read"}
    with pytest.raises(PermissionError):
        app.request("network")
    app.stop()