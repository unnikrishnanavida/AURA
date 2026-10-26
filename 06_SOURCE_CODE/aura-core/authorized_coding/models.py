"""Action models for the authorized-coding workspace workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

__all__ = [
    "ActionName",
    "ResultStatus",
    "InputField",
    "InputSpec",
    "validate_inputs",
    "ApprovalStatus",
    "Approval",
    "ApprovalDecision",
    "AuditDecision",
    "AuditEvent",
    "ActionResult",
]


class ActionName(str, Enum):
    """Project action identifiers (also used as capability names)."""

    LIST_FILES = "project.list_files"
    READ_FILE = "project.read_file"
    WRITE_TEXT = "project.write_text"
    PATCH_FILE = "project.patch_file"
    DELETE_FILE = "project.delete_file"
    CREATE_DIRECTORY = "project.create_directory"
    PROPOSE_CHANGE = "project.propose_change"
    APPLY_CHANGE = "project.apply_change"
    DIFF = "project.diff"
    VERIFY_CHANGE = "project.verify_change"


class ResultStatus(str, Enum):
    """Outcome a caller can act on."""

    SUCCESS = "success"
    ACTION_REQUIRED = "action_required"  # mutation is pending approval
    DENIED = "denied"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


class ApprovalStatus(str, Enum):
    PROPOSED = "proposed"
    EXECUTED = "executed"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class AuditDecision(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    DENIED = "denied"


@dataclass(frozen=True)
class InputField:
    """One field of an action's input schema."""

    name: str
    kind: type[Any]
    required: bool = True
    description: str = ""
    allowed: tuple[Any, ...] = ()


@dataclass(frozen=True)
class InputSpec:
    """Input schema for one action."""

    fields: tuple[InputField, ...] = field(default_factory=tuple)

    def __contains__(self, name: object) -> bool:
        return any(field.name == name for field in self.fields)

    def get(self, name: str) -> InputField | None:
        for field in self.fields:
            if field.name == name:
                return field
        return None


def validate_inputs(inputs: dict[str, Any], spec: InputSpec) -> list[str]:
    """Validate *inputs* against *spec*; return a list of error messages."""
    errors: list[str] = []
    if not isinstance(inputs, dict):
        return ["inputs must be an object"]

    for name, spec_field in spec.fields:
        if name not in inputs:
            if spec_field.required:
                errors.append(f"missing required input {name!r}")
            continue
        value = inputs[name]
        if value is None:
            errors.append(f"input {name!r} may not be None")
            continue
        if not isinstance(value, spec_field.kind):
            errors.append(
                f"input {name!r} must be {getattr(spec_field.kind, '__name__', str(spec_field.kind))}, "
                f"got {type(value).__name__}"
            )
            continue
        if spec_field.allowed and value not in spec_field.allowed:
            errors.append(
                f"input {name!r} must be one of {sorted(spec_field.allowed)!r}, got {value!r}"
            )

    for key in inputs:
        if key not in spec:
            errors.append(f"unexpected input {key!r}")
    return errors


@dataclass(frozen=True)
class Approval:
    """A pending approval record for a mutation. The payload is intentionally
    small and the caller is responsible for redacting *inputs* before storing.
    """

    approval_id: str
    action: ActionName
    actor: str
    workspace_root: str
    proposed_by: str
    inputs: dict[str, Any]
    summary: dict[str, Any]  # machine-readable preview (path, diff, new content)
    status: ApprovalStatus = ApprovalStatus.PROPOSED
    approved_by: str | None = None
    approved_at: str | None = None

    def mark_executed(self, approved_by: str, approved_at: str) -> None:
        self.status = ApprovalStatus.EXECUTED
        self.approved_by = approved_by
        self.approved_at = approved_at

    def mark_rejected(self, reason: str) -> None:
        self.status = ApprovalStatus.REJECTED
        self.approved_by = ""
        self.approved_at = reason


@dataclass(frozen=True)
class ActionResult:
    """One response from the authorized-coding engine."""

    status: ResultStatus
    action: ActionName
    actor: str
    resource: str
    detail: str
    approval_id: str | None = None
    proposed: dict[str, Any] | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class AuditEvent:
    """One recorded audit decision (mirrors :class:`aura.security.audit.AuditRecord`)."""

    action: str
    actor: str
    resource: str
    decision: str
    reason: str
    event_id: str
    correlation_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
