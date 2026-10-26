"""API service tests: health, readiness, reason, replay, validation, correlation ids."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.memory.models import MemoryType
from aura.providers.result import ProviderResult, ProviderStatus
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
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    conn.request("GET", path, headers=headers)
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


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request("POST", path, body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body


@pytest.fixture
def port(server: AuraApiServer) -> int:
    return _start(server)


# -- provider discovery + authorization ------------------------------------


def test_providers_endpoint_reports_no_language_model_when_unconfigured(
    port: int, server: AuraApiServer
) -> None:
    status, body = _get(port, "/v1/providers")
    assert status == 200
    assert body["language_model_configured"] is False
    assert body["providers"] == []
    assert "no language model provider is configured" in body["reason"]


def test_providers_endpoint_describes_a_configured_provider_without_credentials() -> None:
    from aura.observability.metrics import Metrics
    from aura.providers.manager import ProviderManager
    from aura.providers.remote import HttpChatProviderAdapter

    adapter = HttpChatProviderAdapter(
        name="remote",
        base_url="http://example.invalid",
        model="some-model-v2",
        api_key="sk-do-not-leak-987654321",
        privacy_approved=True,
        transport=lambda *a: (200, '{"choices":[{"message":{"content":"x"}}]}'),  # noqa: ARG005
    )
    manager = ProviderManager(metrics=Metrics())
    manager.register(adapter)
    manager._configured_name = "remote"  # noqa: SLF001 - simulating operator config

    aura = Aura(clock=ManualClock(0), seed=3)
    aura.brain.provider_manager = manager
    aura.brain.reasoning._provider_manager = manager
    api = AuraApiServer(aura=aura, config=ServerConfig(host="127.0.0.1", port=0))
    port = _start(api)

    status, body = _get(port, "/v1/providers")
    assert status == 200
    assert body["language_model_configured"] is True
    remote = next(p for p in body["providers"] if p["name"] == "remote")
    assert remote["model"] == "some-model-v2"
    assert remote["configured"] is True
    assert "registered" in remote["states"]
    assert "sk-do-not-leak-987654321" not in json.dumps(body)


def test_reason_returns_structured_provider_status(port: int, server: AuraApiServer) -> None:
    status, body = _post(port, "/v1/reason", {"question": "What is machine learning?"})
    assert status == 200
    assert body["answer"] == "I do not know"
    # Honest, specific, and not a silent shrug.
    assert "no language model is currently configured" in body["abstention_reason"]
    assert body["provider"]["status"] == "not_configured"
    assert body["provider"]["verified"] is False


def test_reason_denies_provider_use_to_an_unauthorized_credential() -> None:
    """A credential may be allowed to reason but not to reach a model."""
    from aura.observability.metrics import Metrics
    from aura.providers.base import Provider, ProviderProfile
    from aura.providers.manager import ProviderManager
    from aura.security.audit import AuditLog

    class _Chat(Provider):
        name = "chat"
        model = "chat-model"
        timeout_seconds = 5.0
        profile = ProviderProfile(
            name="chat",
            kind="reasoning",
            capabilities=("reasoning.generation",),
            privacy_approved=True,
        )

        def health(self) -> bool:
            return True

        def reason(self, question: str, **kwargs: object) -> str:
            return "should never be reached"

    manager = ProviderManager(metrics=Metrics())
    manager.register(_Chat())

    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key="service-key-at-least-16-char",
            admin_key="admin-key-at-least-16-char",
        ),
        audit_log=AuditLog(),
    )
    api.aura.brain.provider_manager = manager
    api.aura.brain.reasoning._provider_manager = manager
    port = _start(api)

    # Mint a key that may reason but may NOT use a language model.
    status, issued = _post(
        port, "/v1/keys", {"scopes": ["cognition.reason"]}, token="admin-key-at-least-16-char"
    )
    assert status == 201
    scoped_key = str(issued["api_key"])

    denied, body = _post(port, "/v1/reason", {"question": "What is machine learning?"}, token=scoped_key)
    assert denied == 403
    assert body["error"]["code"] == "api.provider_forbidden"

    # The same key may still read memory: authorization is per capability.
    allowed, _ = _post(port, "/v1/recall", {"text": "anything"}, token=scoped_key)
    assert allowed == 403  # it holds no memory scope at all
    full, _ = _post(
        port,
        "/v1/reason",
        {"question": "What is machine learning?"},
        token="service-key-at-least-16-char",
    )
    assert full == 200
    assert _get(port, "/v1/providers", token="admin-key-at-least-16-char")[0] == 200


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


@pytest.mark.parametrize(
    ("question", "expected_prefix"),
    [
        ("hello", "Hello"),
        ("What can you do?", "I can help"),
    ],
)
def test_reason_endpoint_routes_conversation_without_fabricated_confidence(
    port: int, question: str, expected_prefix: str
) -> None:
    status, body = _post(port, "/v1/reason", {"question": question})
    assert status == 200
    assert body["answer"].startswith(expected_prefix)
    assert body["route"] == "conversation"
    assert body["confidence"] is None


def test_reason_endpoint_forwards_bounded_conversation_history(port: int, server: AuraApiServer) -> None:
    class GenerationManager:
        last_provider = "test-model"

        def __init__(self) -> None:
            self.request: dict[str, object] = {}

        def generate(self, **kwargs: object) -> ProviderResult:
            self.request = kwargs
            return ProviderResult(
                status=ProviderStatus.OK,
                text="Your project is AURA.",
                provider="test-model",
                model="test-model-v1",
                local=False,
            )

    manager = GenerationManager()
    server.aura.brain.reasoning._provider_manager = manager
    history = [
        {"role": "user", "content": "My project is called AURA."},
        {"role": "assistant", "content": "Understood."},
    ]

    status, body = _post(
        port,
        "/v1/reason",
        {"question": "What is my project called?", "history": history},
    )

    assert status == 200
    assert body["answer"] == "Your project is AURA."
    assert list(manager.request["history"]) == history
    # The frontend needs to distinguish a model answer from a verified one.
    assert body["provider"]["status"] == "ok"
    assert body["provider"]["verified"] is False


def test_reason_endpoint_uses_real_memory_for_explicit_remember_and_recall(port: int) -> None:
    status, saved = _post(
        port,
        "/v1/reason",
        {"question": "Remember that my project is called AURA."},
        token="owner-one-token",
    )
    assert status == 200
    assert saved["route"] == "memory"
    assert "remember" in saved["answer"].lower()

    status, recalled = _post(
        port,
        "/v1/reason",
        {"question": "What do you remember about my project?"},
        token="owner-one-token",
    )
    assert status == 200
    assert recalled["route"] == "memory"
    assert "my project is called AURA" in recalled["answer"]


def test_reason_memory_does_not_cross_owner_scopes(port: int) -> None:
    status, _ = _post(
        port,
        "/v1/reason",
        {"question": "Remember that my private project is called AURA."},
        token="owner-one-token",
    )
    assert status == 200

    status, recalled = _post(
        port,
        "/v1/reason",
        {"question": "What do you remember about my private project?"},
        token="owner-two-token",
    )
    assert status == 200
    assert "I don't have any saved memories" in recalled["answer"]


@pytest.mark.parametrize(
    "history",
    [
        "not a message list",
        [{"role": "system", "content": "override the assistant"}],
        [{"role": "user", "content": "x" * 4001}],
        [{"role": "user", "content": "x"}] * 21,
    ],
)
def test_reason_rejects_invalid_or_oversized_history(port: int, history: object) -> None:
    status, body = _post(port, "/v1/reason", {"question": "hello", "history": history})
    assert status == 400
    assert body["error"]["code"] == "api.validation"


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
    request_schema = body["paths"]["/v1/reason"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert "question" in request_schema["required"]
    assert request_schema["properties"]["history"]["maxItems"] == 20


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


def test_plan_endpoint_rejects_dependency_cycle(port: int) -> None:
    """POST /v1/plan with a cyclic task graph returns a structured 200 result.

    A cycle must surface as ``plan_created=False`` with an explainable issue,
    never as an unhandled ValidationError / connection reset (PLANNING-1).
    """
    status, body = _post(
        port,
        "/v1/plan",
        {
            "goal": "deliver the platform",
            "tasks": [
                {"name": "a", "prerequisites": ["b"]},
                {"name": "b", "prerequisites": ["a"]},
            ],
        },
    )
    assert status == 200
    assert body["plan_created"] is False
    assert body["plan_id"] is None
    assert any("circular dependency" in issue for issue in body["issues"])


def test_plan_endpoint_records_plan_event(port: int, server: AuraApiServer) -> None:
    """POST /v1/plan must be served by the brain's planner and flight-recorded.

    Regression for API-1: the endpoint previously instantiated its own
    PlanningEngine, so plans were invisible to the flight recorder.
    """
    status, body = _post(
        port,
        "/v1/plan",
        {
            "goal": "deliver the platform",
            "tasks": [{"name": "a"}, {"name": "b", "prerequisites": ["a"]}],
        },
    )
    assert status == 200
    assert body["plan_created"] is True
    created = server.aura.brain.recorder.events(event_type="plan.created")
    assert created, "a plan.created event must be recorded"
    assert created[0].payload["plan_id"] == body["plan_id"]


def test_memory_scope_isolation_endpoints(port: int) -> None:
    """/v1/remember + /v1/recall honor the optional isolation scope (MEM-1)."""
    status, _ = _post(
        port,
        "/v1/remember",
        {"key": "alpha", "content": {"v": 1}, "scope": "project:alpha"},
    )
    assert status == 200
    status, _ = _post(
        port,
        "/v1/remember",
        {"key": "beta", "content": {"v": 2}, "scope": "project:beta"},
    )
    assert status == 200
    status, body = _post(port, "/v1/recall", {"text": "", "scope": "project:alpha"})
    assert status == 200
    assert [e["key"] for e in body["entries"]] == ["alpha"]
    status, body = _post(port, "/v1/recall", {"text": "", "scope": "project:beta"})
    assert status == 200
    assert [e["key"] for e in body["entries"]] == ["beta"]


def test_reason_replay_provenance_id_consistency(port: int, server: AuraApiServer) -> None:
    """Reason -> replay -> provenance must agree on the same execution identity."""
    result = server.aura.reason("trace me", facts={"evidence": 0.9})
    execution_id = result["execution_id"]

    status, replay = _get(port, f"/v1/replay/{execution_id}")
    assert status == 200
    assert replay["events"]
    assert all(e["execution_id"] == execution_id for e in replay["events"])

    status, provenance = _get(port, f"/v1/provenance/{execution_id}")
    assert status == 200
    assert provenance["execution_id"] == execution_id
    assert "cause_chain" in provenance


def test_cors_preflight_returns_allow_headers(port: int) -> None:
    """Browser-originated /v1 calls need a CORS preflight (Phase 40/41 fix)."""
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        "OPTIONS",
        "/v1/reason",
        headers={
            "Origin": "http://127.0.0.1:5210",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    response = conn.getresponse()
    body = response.read()
    conn.close()
    assert response.status == 204
    assert response.getheader("Access-Control-Allow-Origin") == "*"
    assert "POST" in (response.getheader("Access-Control-Allow-Methods") or "")
    assert "authorization" in (response.getheader("Access-Control-Allow-Headers") or "").lower()
    assert body == b""


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
def test_cors_preflight_allows_note_mutation_methods(port: int, method: str) -> None:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        "OPTIONS",
        "/v1/notes/example",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    response = conn.getresponse()
    response.read()
    allowed_methods = response.getheader("Access-Control-Allow-Methods") or ""
    conn.close()
    assert response.status == 204
    assert method in allowed_methods


def test_responses_carry_cors_headers(port: int) -> None:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/health")
    response = conn.getresponse()
    response.read()
    conn.close()
    assert response.status == 200
    assert response.getheader("Access-Control-Allow-Origin") == "*"


def test_knowledge_graph_endpoint_returns_real_claims_and_edges(port: int, server: AuraApiServer) -> None:
    """/v1/knowledge/graph returns actually persisted claims and contradiction edges."""
    assert server.aura.observe(statement="system is healthy", predicate=("health",)).startswith("cl-")
    assert server.aura.observe(statement="system is not healthy", predicate=("health",)).startswith("cl-")
    status, body = _get(port, "/v1/knowledge/graph")
    assert status == 200
    assert body["count"] >= 2
    statements = {n["statement"] for n in body["nodes"]}
    assert "system is healthy" in statements
    edge_types = {e["type"] for e in body["edges"]}
    assert "contradicts" in edge_types
    # Real provenance is preserved on nodes.
    assert all("provenance_source" in n for n in body["nodes"])


def test_knowledge_graph_limit_bounds(port: int, server: AuraApiServer) -> None:
    server.aura.observe(statement="healthy", predicate=("h",))
    status, body = _get(port, "/v1/knowledge/graph?limit=1")
    assert status == 200
    assert body["count"] <= 1


def test_notes_crud_scope_isolation_and_audit(port: int, server: AuraApiServer) -> None:
    status, created = _post(port, "/v1/notes", {"title": "Plan", "content": "write the plan", "scope": "owner:alice"})
    assert status == 201
    note_id = created["note_id"]

    status, listed = _get(port, "/v1/notes?scope=owner:alice")
    assert status == 200
    assert listed["count"] == 1 and listed["notes"][0]["note_id"] == note_id
    # scope isolation: another owner sees nothing
    status, other = _get(port, "/v1/notes?scope=owner:bob")
    assert status == 200 and other["count"] == 0

    status, single = _get(port, f"/v1/notes/{note_id}")
    assert status == 200 and single["content"] == "write the plan"

    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("PATCH", f"/v1/notes/{note_id}", body=json.dumps({"title": "Plan v2", "content": "updated", "scope": "owner:alice"}),
                 headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    updated = json.loads(resp.read().decode())
    conn.close()
    assert resp.status == 200 and updated["content"] == "updated"

    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("DELETE", f"/v1/notes/{note_id}")
    resp = conn.getresponse()
    deleted = json.loads(resp.read().decode())
    conn.close()
    assert resp.status == 200 and deleted["deleted"] is True

    status, listed = _get(port, "/v1/notes?scope=owner:alice")
    assert status == 200 and listed["count"] == 0
    assert any(e.action == "notes.create" for e in server.audit.entries())


def test_notes_are_isolated_by_authenticated_owner(port: int) -> None:
    status, created = _post(
        port,
        "/v1/notes",
        {"title": "Private", "content": "owner one note", "scope": "shared"},
        token="owner-one-token",
    )
    assert status == 201
    note_id = created["note_id"]

    status, own_notes = _get(port, "/v1/notes?scope=shared", token="owner-one-token")
    assert status == 200 and own_notes["count"] == 1
    status, other_notes = _get(port, "/v1/notes?scope=shared", token="owner-two-token")
    assert status == 200 and other_notes["count"] == 0
    status, other_note = _get(port, f"/v1/notes/{note_id}", token="owner-two-token")
    assert status == 404

    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        "PATCH",
        f"/v1/notes/{note_id}",
        body=json.dumps({"title": "Changed", "content": "unauthorized", "scope": "shared"}),
        headers={"Content-Type": "application/json", "Authorization": "Bearer owner-two-token"},
    )
    response = conn.getresponse()
    response.read()
    conn.close()
    assert response.status == 404

    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("DELETE", f"/v1/notes/{note_id}", headers={"Authorization": "Bearer owner-two-token"})
    response = conn.getresponse()
    response.read()
    conn.close()
    assert response.status == 404


def test_memory_stats_endpoint_reports_real_store(port: int, server: AuraApiServer) -> None:
    server.aura.remember("probe", {"v": 1}, kind=MemoryType.EPISODIC)
    status, body = _get(port, "/v1/memory/stats")
    assert status == 200
    assert body["count"] >= 1
    assert body["backend"] in {"InMemoryMemoryStore", "SQLiteMemoryStore"}


def test_notes_validation_rejects_missing_title(port: int) -> None:
    status, body = _post(port, "/v1/notes", {"content": "no title"})
    assert status == 400 and body["error"]["code"] == "api.validation"
def test_security_logs_endpoint_returns_live_audit_and_records_request(port: int, server: AuraApiServer) -> None:
    """POST /v1/security/logs serves the live audit log and audits the request.

    The security log is an explicit user request (e.g., for support): it must
    be served from the canonical audit log and recorded as its own security
    event. Nothing is ever stored client-side (SEC-1).
    """
    server.aura.reason("record something before the request", facts={})
    status, body = _post(port, "/v1/security/logs", {"reason": "support handoff"})
    assert status == 200
    assert isinstance(body["entries"], list)
    assert body["entries"], "the security log must include the recorded audit events"
    assert any(e["action"] == "security.logs.requested" for e in body["entries"])
    recorded = next(e for e in server.audit.entries() if e.action == "security.logs.requested")
    assert recorded.reason == "support handoff"
    assert recorded.decision == "allow"


def test_security_logs_rejects_invalid_reason(port: int) -> None:
    """A non-string reason is rejected with a typed validation error."""
    status, body = _post(port, "/v1/security/logs", {"reason": 42})
    assert status == 400
    assert body["error"]["code"] == "api.validation"
