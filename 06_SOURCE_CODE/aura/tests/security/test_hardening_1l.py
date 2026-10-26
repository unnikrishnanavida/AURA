"""Phase 1L security regression suite.

Targets the newest canonical surface (1K automation) with adversarial tests
through a *secured* HTTP server (a real authorization boundary), because the
existing automation/API tests only exercise local-first (no-credential) mode.

Covers:
  * authentication enforcement when a boundary is configured (401)
  * insufficient-scope denial (403)
  * cross-owner isolation at the HTTP layer (404, no existence leak)
  * checkpoint/non-authority invariant (a checkpoint is task state, not a token)
  * replayed lifecycle requests stay coherent (fail closed)
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest

from aura.api.security import check_request_size
from aura.api.server import AuraApiServer, ServerConfig
from aura.automation import AutomationManager, AutomationStep, automation_available
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura
from aura.security.audit import AuditLog

pytestmark = pytest.mark.skipif(not automation_available(), reason="agents runtime not installed")

ADMIN_KEY = "admin-key-at-least-16-char"
SERVICE_KEY = "service-key-at-least-16-char"


def _secure_server() -> tuple[AuraApiServer, int]:
    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=3),
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key=SERVICE_KEY,
            admin_key=ADMIN_KEY,
            rate_burst=200,
            rate_per_second=100.0,
            max_request_bytes=1024,
        ),
        audit_log=AuditLog(),
    )
    wrapped = api._handler()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), wrapped)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd
    return api, httpd.server_port


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=30)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request("POST", path, body=json.dumps(payload), headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def _get(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=30)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    conn.request("GET", path, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def _issue_scoped_key(port: int, *scopes: str) -> str:
    status, body = _post(port, "/v1/keys", {"scopes": list(scopes)}, token=ADMIN_KEY)
    assert status == 201, body
    return str(body["api_key"])
# -- authentication boundary enforcement -----------------------------------


def test_automation_requires_auth_when_boundary_configured() -> None:
    _api, port = _secure_server()
    status, body = _get(port, "/v1/automation/tasks")
    assert status == 401 and body["error"]["code"] == "api.auth_failed"
    status, body = _post(port, "/v1/automation/tasks", {"goal": "x"})
    assert status == 401 and body["error"]["code"] == "api.auth_failed"


def test_automation_rejects_wrong_credential() -> None:
    _api, port = _secure_server()
    status, body = _post(port, "/v1/automation/tasks", {"goal": "x"}, token="wrong-key-not-16")
    assert status == 401 and body["error"]["code"] == "api.auth_failed"


def test_automation_insufficient_scope_is_denied() -> None:
    _api, port = _secure_server()
    # This key holds only memory.read; automation needs agents.run.
    key = _issue_scoped_key(port, "memory.read")
    status, body = _post(port, "/v1/automation/tasks", {"goal": "x"}, token=key)
    assert status == 403 and body["error"]["code"] == "api.forbidden"
    status, body = _get(port, "/v1/automation/tasks", token=key)
    assert status == 403 and body["error"]["code"] == "api.forbidden"


def test_automation_scoped_key_is_allowed() -> None:
    _api, port = _secure_server()
    key = _issue_scoped_key(port, "agents.run")
    status, body = _post(port, "/v1/automation/tasks", {"goal": "echo-world"}, token=key)
    assert status == 201


# -- cross-owner isolation --------------------------------------------------


def test_automation_cross_owner_isolation() -> None:
    """Owner A creates a task; owner B can never observe or act on it."""
    _api, port = _secure_server()
    alice = _issue_scoped_key(port, "agents.run")
    bob = _issue_scoped_key(port, "agents.run")

    status, created = _post(port, "/v1/automation/tasks", {"goal": "echo-world"}, token=alice)
    assert status == 201
    task_id = created["task_id"]

    # Bob cannot list Alice's task ...
    _, ls = _get(port, "/v1/automation/tasks", token=bob)
    assert all(t["task_id"] != task_id for t in ls["tasks"])
    # ... nor inspect, run, cancel, resume, retry, or read checkpoints.
    for path in (f"/v1/automation/tasks/{task_id}", f"/v1/automation/tasks/{task_id}/checkpoints"):
        status, _ = _get(port, path, token=bob)
        assert status == 404, f"{path} leaked to another owner"
    for action in ("run", "cancel", "pause", "resume", "retry"):
        status, _ = _post(port, f"/v1/automation/tasks/{task_id}/{action}", {}, token=bob)
        assert status == 404, f"{action} leaked to another owner"

    # Alice can still observe her own task (same task id, correct owner).
    status, _ = _get(port, f"/v1/automation/tasks/{task_id}", token=alice)
    assert status == 200


def test_automation_unknown_and_other_owner_ids_fail_closed() -> None:
    """A non-existent task and another owner's task are indistinguishable."""
    _api, port = _secure_server()
    alice = _issue_scoped_key(port, "agents.run")
    bob = _issue_scoped_key(port, "agents.run")
    _, created = _post(port, "/v1/automation/tasks", {"goal": "echo"}, token=alice)
    task_id = created["task_id"]

    # Bob requesting an unknown id and requesting Alice's id both fail closed.
    s_unknown, _ = _get(port, "/v1/automation/tasks/task-zzz", token=bob)
    s_foreign, _ = _get(port, f"/v1/automation/tasks/{task_id}", token=bob)
    assert s_unknown == 404
    assert s_foreign == 404

    # Malformed/guessable ids never crash and never surface another's task.
    for bad in ("task-1", "task-../..", "task-%2e%2e", "ALL", "..%2fsecret"):
        status, _ = _get(port, f"/v1/automation/tasks/{bad}", token=bob)
        assert status in {400, 401, 403, 404}
# -- non-authority invariant -------------------------------------------------


def test_checkpoint_never_carries_authority() -> None:
    """Checkpoints are historical task state, not authorization tokens."""
    _api, port = _secure_server()
    alice = _issue_scoped_key(port, "agents.run")
    status, created = _post(
        port, "/v1/automation/tasks", {"goal": "echo-world", "steps": ["a", "b"]}, token=alice
    )
    assert status == 201
    task_id = created["task_id"]
    _, cps = _get(port, f"/v1/automation/tasks/{task_id}/checkpoints", token=alice)
    assert isinstance(cps["checkpoints"], list)
    for cp in cps["checkpoints"]:
        rendered = json.dumps(cp)
        for bad in ("approved", "grant", "capabilities", "secret", "password", "api_key", "owner_override"):
            assert bad not in rendered, f"checkpoint carried authority/secret field {bad!r}"


def test_replayed_lifecycle_stays_coherent_after_cancel() -> None:
    """run/cancel/run/retry on a cancelled task must stay terminal, never resurrect."""
    _api, port = _secure_server()
    key = _issue_scoped_key(port, "agents.run")
    _, created = _post(port, "/v1/automation/tasks", {"goal": "echo-world"}, token=key)
    task_id = created["task_id"]

    status, cancelled = _post(port, f"/v1/automation/tasks/{task_id}/cancel", {}, token=key)
    assert status == 200 and cancelled["state"] == "cancelled"

    # Replaying run/retry/pause/resume on a terminal task must not resurrect it.
    for action in ("run", "retry", "pause", "resume"):
        status, out = _post(port, f"/v1/automation/tasks/{task_id}/{action}", {}, token=key)
        assert status == 200
        assert out["state"] == "cancelled", f"{action} resurrected a cancelled task"


def test_oversized_automation_payload_rejected() -> None:
    assert check_request_size(10) is True  # the wall exists; small payloads pass
    _api, port = _secure_server()
    key = _issue_scoped_key(port, "agents.run")
    big_steps = [f"step-{i}" for i in range(21)]  # > the documented 20-step bound
    status, body = _post(port, "/v1/automation/tasks", {"goal": "x", "steps": big_steps}, token=key)
    assert status == 400 and body["error"]["code"] == "api.validation"


# -- manager-level re-authorization invariant --------------------------------


def test_manager_run_requires_current_owner_not_checkpoint_owner() -> None:
    """Resume re-checks the *caller* identity; a stored checkpoint grants nothing."""
    mgr = AutomationManager(runner=lambda step, task, token=None, **_: None)
    mgr.submit(owner="owner:alice", description="d", steps=[AutomationStep(goal="echo")])
    task_id = next(iter(mgr._tasks))

    # A different owner cannot act on Alice's task even though its checkpoints
    # are stored server-side; only the matching owner resolves it.
    assert mgr.get(task_id, owner="owner:bob") is None
    assert mgr.run(task_id, owner="owner:bob") is None
    assert mgr.cancel(task_id, owner="owner:bob") is None
    got = mgr.get(task_id, owner="owner:alice")
    assert got is not None and got["task_id"] == task_id