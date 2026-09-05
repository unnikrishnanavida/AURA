"""Unit tests for aura-api core: redaction, auth, authorization, rate limits, versioning."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_api import (
    ApiKeyStore,
    Authenticator,
    Authorizer,
    RBACPolicy,
    SlidingWindow,
    TokenBucket,
    VersionRegistry,
)
from aura_api.auth.authenticator import ApiKeyCredential
from aura_api.core.context import Principal
from aura_api.core.errors import (
    AuthenticationError,
    AuthorizationError,
    ProblemDetails,
    ValidationError,
    redact,
)


def test_redact_secrets():
    assert "sk-secretkey1234567890" not in redact("token sk-secretkey1234567890 leaked")
    assert "api_key=<redacted>" in redact("api_key = super-secret-abc")
    assert redact("bearer abc12345") == "bearer <redacted>"


def test_problem_details_redacts():
    problem = ProblemDetails(
        title="auth",
        status=401,
        code="api.auth_failed",
        detail="credential sk-abcdef123456789 is invalid",
        correlation_id="co-1",
    )
    payload = problem.to_dict()
    assert "sk-abcdef123456789" not in payload["detail"]


def test_api_key_hash_never_stores_plaintext():
    store = ApiKeyStore()
    store.register("k1", "super-secret", subject="alice")
    record = store.get("k1")
    assert record.key_hash != "super-secret"
    assert "super-secret" not in record.key_hash


def test_authenticator_rejects_unknown_key():
    store = ApiKeyStore()
    auth = Authenticator(store)
    with pytest.raises(AuthenticationError):
        auth.authenticate(ApiKeyCredential("k-unknown.secret"))


def test_authenticator_accepts_valid_key():
    store = ApiKeyStore()
    store.register("k1", "secret", subject="alice", roles=("writer",))
    auth = Authenticator(store)
    principal = auth.authenticate(ApiKeyCredential("k1.secret"))
    assert principal.subject == "alice"
    assert principal.roles == ("writer",)


def test_authenticator_rejects_disabled_key():
    store = ApiKeyStore()
    store.register("k1", "secret", subject="alice")
    store.records["k1"] = __import__("dataclasses").replace(store.records["k1"], enabled=False)
    auth = Authenticator(store)
    with pytest.raises(AuthenticationError):
        auth.authenticate(ApiKeyCredential("k1.secret"))


def test_rbac_denies_unknown_role():
    rbac = RBACPolicy()
    rbac.grant(role="writer", resource_type="echo", action="create")
    assert rbac.check(Principal("alice", roles=("reader",)), "echo", "create") is False
    assert rbac.check(Principal("alice", roles=("writer",)), "echo", "create") is True


def test_authorizer_fails_closed_for_anonymous():
    authorizer = Authorizer(rbac=RBACPolicy())
    with pytest.raises(AuthorizationError):
        authorizer.authorize(None, "echo", "create")  # type: ignore[arg-type]


def test_token_bucket_refills():
    bucket = TokenBucket(capacity=1.0, refill_per_second=2.0)
    assert bucket.allow("a", now=0.0) is True
    assert bucket.allow("a", now=0.1) is False  # not enough elapsed to refill
    assert bucket.allow("a", now=0.6) is True  # refilled


def test_sliding_window_limits():
    window = SlidingWindow(max_requests=2, window_seconds=10.0)
    assert window.allow("a", now=0.0) is True
    assert window.allow("a", now=1.0) is True
    assert window.allow("a", now=2.0) is False
    assert window.allow("a", now=11.0) is True  # window slid


def test_version_registry_resolves():
    registry = VersionRegistry()
    assert registry.resolve("", from_path="/v2/echo") == "v2"
    assert registry.resolve("") == "v1"


def test_version_registry_rejects_unknown():
    registry = VersionRegistry()
    with pytest.raises(ValidationError):
        registry.resolve("v99")