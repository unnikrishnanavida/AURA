"""Authorization unit tests: scope resolution and matching.

These need no HTTP server — they pin the rules that the API layer depends on,
including the guard that stops a new route shipping without a scope.
"""

from __future__ import annotations

from aura.api.authorization import (
    ALL_SCOPES,
    ROUTE_SCOPES,
    Credential,
    required_scope,
    scope_allows,
)
from aura.api.server import OPENAPI

# -- scope matching ---------------------------------------------------------


def test_wildcard_grant_allows_everything() -> None:
    assert scope_allows(("*",), "memory.write")
    assert scope_allows(["*"], "admin.keys")


def test_prefix_wildcard_grants_only_its_family() -> None:
    assert scope_allows(("memory.*",), "memory.read")
    assert scope_allows(("memory.*",), "memory.write")
    assert not scope_allows(("memory.*",), "knowledge.read")
    assert not scope_allows(("memory.*",), "memory")  # no partial-segment match


def test_exact_scope_does_not_grant_its_siblings() -> None:
    assert scope_allows(("memory.read",), "memory.read")
    assert not scope_allows(("memory.read",), "memory.write")


def test_empty_grant_denies_everything() -> None:
    # Deny by default: absence of evidence is never permission.
    assert not scope_allows((), "memory.read")
    assert not scope_allows([], "cognition.reason")


def test_credential_allows_uses_its_scopes() -> None:
    credential = Credential(kind="issued", subject="kid-1", scopes=("notes.read",), owner="o")
    assert credential.allows("notes.read")
    assert not credential.allows("notes.write")


def test_credential_public_dict_never_exposes_a_secret() -> None:
    credential = Credential(kind="issued", subject="kid-1", scopes=("memory.read",), owner="o")
    public = credential.to_public_dict()
    assert public == {"kind": "issued", "subject": "kid-1", "scopes": ["memory.read"]}


# -- route mapping ----------------------------------------------------------


def test_exact_routes_resolve_to_their_scope() -> None:
    assert required_scope("POST", "/v1/reason") == "cognition.reason"
    assert required_scope("POST", "/v1/remember") == "memory.write"
    assert required_scope("GET", "/v1/audit") == "security.audit"
    assert required_scope("POST", "/v1/keys") == "admin.keys"


def test_method_matters_for_the_same_path() -> None:
    assert required_scope("GET", "/v1/notes") == "notes.read"
    assert required_scope("POST", "/v1/notes") == "notes.write"
    assert required_scope("DELETE", "/v1/notes") is None  # only sub-resources are mapped


def test_subtree_routes_resolve() -> None:
    assert required_scope("GET", "/v1/notes/note-1") == "notes.read"
    assert required_scope("DELETE", "/v1/notes/note-1") == "notes.write"
    assert required_scope("GET", "/v1/replay/abc") == "provenance.read"


def test_longest_prefix_wins() -> None:
    # A specific subtree must never be shadowed by a broader one.
    assert required_scope("GET", "/v1/notes/a/b") == "notes.read"
    assert required_scope("GET", "/v1/sessions/s1") == "sessions.manage"


def test_unknown_routes_declare_no_scope_but_still_need_auth() -> None:
    # Returning None means "no scope declared"; the caller is still required to
    # authenticate. Anything else would silently invent permission.
    assert required_scope("POST", "/v1/not-a-route") is None


def test_every_declared_scope_is_in_the_published_set() -> None:
    for (_method, _path), scope in ROUTE_SCOPES.items():
        assert scope in ALL_SCOPES, f"{scope!r} is not published in ALL_SCOPES"


def test_every_documented_api_path_has_a_scope() -> None:
    """Drift guard: a new documented route cannot ship without a scope."""
    missing = []
    for path, operations in OPENAPI["paths"].items():
        if not path.startswith("/v1/"):
            continue
        for method in operations:
            if required_scope(method.upper(), path) is None:
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"documented routes missing a scope: {missing}"