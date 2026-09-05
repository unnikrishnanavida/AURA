"""Tests for the aura-api security pipeline and reference processor."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from aura_api import (
    ApiKeyStore,
    Authenticator,
    Authorizer,
    RBACPolicy,
    ReferenceApi,
    TokenBucket,
)


def build_api(*, rate_capacity: float = 10.0, rate_refill: float = 10.0) -> ReferenceApi:
    store = ApiKeyStore()
    store.register("k1", "secret", subject="alice", roles=("writer",))
    store.register("k2", "secret2", subject="bob", roles=("reader",))
    rbac = RBACPolicy()
    rbac.grant(role="writer", resource_type="echo", action="create")
    rbac.grant(role="reader", resource_type="echo", action="read")
    return ReferenceApi(
        authenticator=Authenticator(store),
        authorizer=Authorizer(rbac=rbac),
        limiter=TokenBucket(rate_capacity, rate_refill),
    )


AUTH = {"authorization": "Bearer k1.secret"}


def test_health_endpoint():
    api = build_api()
    resp = api.handle(method="GET", path="/health")
    assert resp.status == 200
    assert resp.body["status"] == "ok"
    assert resp.correlation_id  # correlation always present


def test_readiness_endpoint_defaults_ready():
    api = build_api()
    resp = api.handle(method="GET", path="/ready")
    assert resp.status == 200
    assert resp.body["status"] == "ready"


def test_readiness_fails_closed_when_dependency_down():
    api = build_api()
    api.health.register("db", lambda: (False, "connection refused"))
    resp = api.handle(method="GET", path="/ready")
    assert resp.status == 503
    assert resp.body["status"] == "not_ready"


def test_successful_authenticated_echo():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={**AUTH, "x-correlation-id": "co-test-1"},
        body={"message": "hello"},
    )
    assert resp.status == 200
    assert resp.body["data"]["echo"] == "hello"
    assert resp.body["data"]["subject"] == "alice"
    assert resp.body["correlation_id"] == "co-test-1"


def test_missing_credentials_fails_closed():
    api = build_api()
    resp = api.handle(method="POST", path="/v1/echo", headers={}, body={"message": "hi"})
    assert resp.status == 401
    assert resp.body["error"]["code"] == "api.auth_failed"
    assert "correlation_id" in resp.body["error"]


def test_invalid_secret_fails_closed():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer k1.wrong"},
        body={"message": "hi"},
    )
    assert resp.status == 401
    assert resp.body["error"]["code"] == "api.auth_failed"


def test_malformed_credential_fails_closed():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer not-a-valid-key"},
        body={"message": "hi"},
    )
    assert resp.status == 401


def test_authorization_failure_fails_closed():
    """bob is reader; echoing requires the create action -> 403."""
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer k2.secret2"},
        body={"message": "hi"},
    )
    assert resp.status == 403
    assert resp.body["error"]["code"] == "api.forbidden"


def test_invalid_request_structured_error():
    api = build_api()
    resp = api.handle(method="POST", path="/v1/echo", headers=AUTH, body={"message": ""})
    assert resp.status == 400
    assert resp.body["error"]["code"].startswith("api.")  # structured validation error


def test_missing_field_structured_error():
    api = build_api()
    resp = api.handle(method="POST", path="/v1/echo", headers=AUTH, body={})
    assert resp.status == 400
    assert resp.body["error"]["code"] == "api.missing_field"


def test_malformed_payload_structured_error():
    api = build_api()
    resp = api.handle(method="POST", path="/v1/echo", headers=AUTH, body=b"this is not json{")
    assert resp.status == 400
    assert resp.body["error"]["code"] == "api.malformed_payload"


def test_unknown_endpoint_structured_404():
    api = build_api()
    resp = api.handle(method="GET", path="/nope")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "api.not_found"


def test_unsupported_version_rejected():
    api = build_api()
    resp = api.handle(method="POST", path="/v9/echo", headers=AUTH, body={"message": "hi"})
    assert resp.status == 400
    assert resp.body["error"]["code"] == "api.unsupported_version"


def test_rate_limit_exceeded_returns_429():
    api = build_api(rate_capacity=2.0, rate_refill=0.0)
    ok1 = api.handle(method="POST", path="/v1/echo", headers=AUTH, body={"message": "a"})
    ok2 = api.handle(method="POST", path="/v1/echo", headers=AUTH, body={"message": "b"})
    denied = api.handle(method="POST", path="/v1/echo", headers=AUTH, body={"message": "c"})
    assert ok1.status == 200
    assert ok2.status == 200
    assert denied.status == 429
    assert denied.body["error"]["code"] == "api.rate_limited"


def test_secret_never_leaks_in_error():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer sk-secretkey1234567890"},
        body={"message": "hi"},
    )
    raw = str(resp.body)
    assert "sk-secretkey1234567890" not in raw


def test_audit_records_denied_auth():
    api = build_api()
    api.handle(method="POST", path="/v1/echo", headers={}, body={"message": "hi"})
    events = api.audit.events()
    assert any(e.event_type == "api_error" for e in events)


def test_security_headers_present():
    api = build_api()
    resp = api.handle(method="GET", path="/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("cache-control") == "no-store"