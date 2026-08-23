"""Kernel package exports for the AURA memory subsystem.

This package exposes the permission engine and supporting policy types used by the
memory runtime.  The exports are intentionally lightweight so other modules can
import the public API without depending on the implementation module directly.
"""

from __future__ import annotations

from typing import List

from .permissions import PermissionAuditEntry, PermissionDecision, PermissionRule, Permissions

__all__: List[str] = [
    "PermissionAuditEntry",
    "PermissionDecision",
    "PermissionRule",
    "Permissions",
]

__version__ = "0.1.0"
