"""Authorized coding: project actions with approval, workspace boundary, and audit.

This package is the smallest missing piece of the "authorized coding" workflow:
it adds a *policy-enforced*, *approval-gated*, *boundary-checked*, *audited*
set of project actions on top of the existing AURA contracts. It reuses the
existing audit and redaction contracts (see :mod:`aura.security.audit` and
:class:`SecretRedactor`), and adds no second registry or persistence layer --
the in-memory approval store below is the workflow's transient state, wired
to the existing :class:` AuditLog` and :class:`SecretRedactor`.
"""

from .redaction import SecretRedactor, redact_payload

__all__ = [
    "SecretRedactor",
    "redact_payload",
]

__version__ = "0.1.0"
