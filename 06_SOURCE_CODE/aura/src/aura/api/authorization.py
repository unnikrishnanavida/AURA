"""Authorization for the HTTP boundary: authentication is not authorization.

A credential proves *who* is calling. A scope decides *what* they may do. This
module is the single authority for the second question, so no individual route
handler can forget to ask for one.

Design rules:

- **One table.** Every route's required scope lives in :data:`ROUTE_SCOPES`.
  The server looks the scope up centrally from the request, so adding a route
  without a scope is caught by a test rather than by a breach.
- **The project's own vocabulary.** Scope names are dotted capability names in
  the same style the engine already uses (``memory.read``, ``domain.execute``,
  ``filesystem.read``), not invented role names.
- **Wildcards, through the existing matcher.** Matching reuses
  :func:`aura.security.capabilities.name_matches`, so a grant of ``memory.*``
  or ``*`` behaves exactly as capability matching already defines.
- **Deny by default.** A key with no scopes, or one that lacks the required
  scope, is denied. Absence of evidence is never permission.
- **Fail open only when there is no security boundary at all.** When the server
  has no configured credential, the local-first single-user mode keeps working
  unchanged; that mode has no scopes to enforce because it has no identities.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura.security.capabilities import name_matches

#: Every scope AURA issues, for documentation and validation.
ALL_SCOPES: tuple[str, ...] = (
    "cognition.reason",
    "memory.read",
    "memory.write",
    "knowledge.read",
    "knowledge.write",
    "research.run",
    "research.read",
    "plan.create",
    "notes.read",
    "notes.write",
    "execute.run",
    "provenance.read",
    "ops.metrics",
    "security.audit",
    "sessions.manage",
    "admin.keys",
    "providers.use",
    "providers.read",
    "agents.run",
)

#: ``(method, path) -> required scope``. Paths may end in ``*`` to match a
#: subtree; the table is intentionally explicit so a new route is a visible,
#: reviewable addition rather than an implicit inheritance.
ROUTE_SCOPES: dict[tuple[str, str], str] = {
    ("GET", "/health"): "ops.metrics",
    ("GET", "/ready"): "ops.metrics",
    ("POST", "/v1/reason"): "cognition.reason",
    ("POST", "/v1/remember"): "memory.write",
    ("POST", "/v1/recall"): "memory.read",
    ("GET", "/v1/memory/stats"): "memory.read",
    ("POST", "/v1/observe"): "knowledge.write",
    ("POST", "/v1/retrieve"): "knowledge.read",
    ("GET", "/v1/knowledge/graph"): "knowledge.read",
    ("POST", "/v1/research"): "research.run",
    ("GET", "/v1/research/runs"): "research.read",
    ("POST", "/v1/plan"): "plan.create",
    ("GET", "/v1/notes"): "notes.read",
    ("POST", "/v1/notes"): "notes.write",
    ("PATCH", "/v1/notes/*"): "notes.write",
    ("DELETE", "/v1/notes/*"): "notes.write",
    ("GET", "/v1/notes/*"): "notes.read",
    ("GET", "/v1/sessions"): "sessions.manage",
    ("POST", "/v1/sessions"): "sessions.manage",
    ("GET", "/v1/sessions/*"): "sessions.manage",
    ("DELETE", "/v1/sessions/*"): "sessions.manage",
    ("GET", "/v1/metrics"): "ops.metrics",
    ("GET", "/v1/audit"): "security.audit",
    ("POST", "/v1/security/logs"): "security.audit",
    ("GET", "/v1/provenance/*"): "provenance.read",
    ("GET", "/v1/replay/*"): "provenance.read",
    ("POST", "/v1/pipeline"): "execute.run",
("GET", "/v1/tasks/*"): "cognition.reason",
    ("POST", "/v1/tasks/*"): "cognition.reason",
    ("POST", "/v1/agents/run"): "agents.run",
    # Phase 1K automation: orchestrates guarded agent tasks; ownership is
    # enforced server-side, so the read/manage surface reuses the agents scope.
    ("GET", "/v1/automation/tasks"): "agents.run",
    ("POST", "/v1/automation/tasks"): "agents.run",
    ("GET", "/v1/automation/tasks/*"): "agents.run",
    ("POST", "/v1/automation/tasks/*"): "agents.run",
    ("POST", "/v1/keys"): "admin.keys",
    ("POST", "/v1/keys/revoke"): "admin.keys",
    ("GET", "/v1/providers"): "providers.read",
}

#: Granted to the bootstrap static credential when one is configured.
STATIC_SCOPES: tuple[str, ...] = ("*",)

#: Granted to the admin key: it may issue and revoke keys.
ADMIN_SCOPES: tuple[str, ...] = ("*",)


@dataclass(frozen=True, slots=True)
class Credential:
    """An authenticated caller: what it is, and what it is allowed to do."""

    kind: str  # "static" | "issued" | "admin" | "anonymous"
    subject: str
    scopes: tuple[str, ...]
    owner: str

    def allows(self, required: str) -> bool:
        return scope_allows(self.scopes, required)

    def to_public_dict(self) -> dict[str, object]:
        """Safe for diagnostics: identity and scopes, never the secret."""
        return {"kind": self.kind, "subject": self.subject, "scopes": list(self.scopes)}


def scope_allows(granted: tuple[str, ...] | list[str], required: str) -> bool:
    """True when any granted scope satisfies ``required``."""
    return any(name_matches(pattern, required) for pattern in granted)


def required_scope(method: str, path: str) -> str | None:
    """The scope a request needs, or ``None`` when the route declares none."""
    candidate = (method.upper(), path)
    if candidate in ROUTE_SCOPES:
        return ROUTE_SCOPES[candidate]
    # Subtree match: the most specific (longest) prefix wins, so
    # "/v1/notes/*" cannot be shadowed by a catch-all.
    best: tuple[int, str] | None = None
    for (route_method, pattern), scope in ROUTE_SCOPES.items():
        if route_method != candidate[0] or not pattern.endswith("/*"):
            continue
        prefix = pattern[:-1]
        if path.startswith(prefix) and (best is None or len(prefix) > best[0]):
            best = (len(prefix), scope)
    return best[1] if best else None


__all__ = [
    "ADMIN_SCOPES",
    "ALL_SCOPES",
    "ROUTE_SCOPES",
    "STATIC_SCOPES",
    "Credential",
    "required_scope",
    "scope_allows",
]
