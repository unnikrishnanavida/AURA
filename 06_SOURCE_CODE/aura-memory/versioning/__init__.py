"""Versioning utilities for aura-memory."""

try:
    from ..core.constants import APP_VERSION
except ImportError:  # pragma: no cover - fallback for direct imports
    from core.constants import APP_VERSION


def get_version() -> str:
    return APP_VERSION


__all__ = ["get_version"]
