"""Core exception types for AURA Memory."""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional


class AuraError(Exception):
    """Base exception for the AURA system."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}
        self.trace = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        return {"message": str(self), "context": self.context, "trace": self.trace}


class ValidationError(AuraError):
    """Raised when validation fails."""


class NotFoundError(AuraError):
    """Raised when an entity is not found."""


__all__ = ["AuraError", "ValidationError", "NotFoundError"]
