"""Domain error taxonomy for aura-knowledge.

All errors subclass :class:`KnowledgeError` so callers can handle knowledge
failures uniformly. Every error carries a stable machine-readable ``code``.
"""

from __future__ import annotations


class KnowledgeError(Exception):
    """Base class for all aura-knowledge domain errors."""

    code = "knowledge.error"

    def __init__(self, message: str, *, correlation_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.correlation_id = correlation_id

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class ClaimNotFoundError(KnowledgeError):
    """No claim exists with the requested id."""

    code = "knowledge.claim_not_found"


class SourceNotFoundError(KnowledgeError):
    """No source exists with the requested identifier."""

    code = "knowledge.source_not_found"


class EvidenceNotFoundError(KnowledgeError):
    """No evidence exists with the requested id."""

    code = "knowledge.evidence_not_found"


class ValidationError(KnowledgeError):
    """A domain object or argument failed validation."""

    code = "knowledge.validation_failed"


class VerificationBlockedError(KnowledgeError):
    """Verification was requested but preconditions block it (e.g. conflict)."""

    code = "knowledge.verification_blocked"


class RevisionNotAllowedError(KnowledgeError):
    """A belief revision operation was rejected by policy."""

    code = "knowledge.revision_denied"


class UnsupportedOperationError(KnowledgeError):
    """The operation is not supported by this knowledge engine."""

    code = "knowledge.unsupported_operation"


__all__ = [
    "ClaimNotFoundError",
    "EvidenceNotFoundError",
    "KnowledgeError",
    "RevisionNotAllowedError",
    "SourceNotFoundError",
    "UnsupportedOperationError",
    "ValidationError",
    "VerificationBlockedError",
]