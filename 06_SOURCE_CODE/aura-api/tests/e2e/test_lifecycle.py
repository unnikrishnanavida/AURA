"""End-to-end lifecycle test for aura-api.

Demonstrates a full request lifecycle: correlation ID generation,
authentication, authorization, rate limiting, validation, structured
response, audit trail, and observability of the whole pass.
"""

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


def build_api() -> ReferenceApi:
    store = ApiKeyStore()
    store.register("svc-1", "s3cret", subject="service", roles=("operator",))
    rbac = RBACPolicy()
    rbac.grant(role="operator", resource_type="echo", action="create")
    return ReferenceApi(
        authenticator=Authenticator(store),
        authorizer=Authorizer(rbac=rbac),
        limiter=TokenBucket(100, 100),
    )


def test_full_request_lifecycle():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer svc-1.s3cret"},
        body={"message": "hello lifecycle"},
        client_ip="10.0.0.5",
    )
    assert resp.status == 200
    assert resp.body["data"]["echo"] == "hello lifecycle"
    assert resp.body["data"]["subject"] == "service"
    assert resp.correlation_id.startswith("co-")
    # security headers on a successful response too
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_lifecycle_denial_is_audited_and_correlated():
    api = build_api()
    resp = api.handle(
        method="POST",
        path="/v1/echo",
        headers={"authorization": "Bearer svc-1.wrong-secret"},
        body={"message": "x"},
        client_ip="10.0.0.9",
    )
    assert resp.status == 401
    correlation = resp.correlation_id
    assert correlation.startswith("co-")
    # the audit trail captures the denial, correlated
    related = api.audit.for_correlation(correlation)
    assert related, "denial must be audited with its correlation id"
    assert related[0].outcome == "denied"


def test_observability_via_audit_trail_ordered():
    api = build_api()
    api.handle(method="GET", path="/health")
    api.handle(method="GET", path="/ready")
    events = api.audit.events()
    # health/ready succeed without audit entries; a denied request adds one
    before = len(events)
    api.handle(method="POST", path="/v1/echo", headers={}, body={"message": "x"})
    after = len(api.audit.events())
    assert after == before + 1