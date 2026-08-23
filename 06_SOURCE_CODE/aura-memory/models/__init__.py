"""Model helpers for aura-memory."""

try:
    from ..core.models import BaseModel
except ImportError:  # pragma: no cover - fallback for direct imports
    from core.models import BaseModel

__all__ = ["BaseModel"]
