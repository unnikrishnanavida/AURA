"""Exceptions package for aura-memory."""

try:
    from ..core.exceptions import AuraError, NotFoundError, ValidationError
except ImportError:  # pragma: no cover - fallback for direct imports
    from core.exceptions import AuraError, NotFoundError, ValidationError

__all__ = ["AuraError", "ValidationError", "NotFoundError"]
