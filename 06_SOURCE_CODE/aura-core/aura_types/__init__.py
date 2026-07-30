"""Aura-specific typed aliases and primitives.

This package replaces the generic `types` package to avoid colliding
with the Python standard library module of the same name.
"""

from .primitives import ID
from .common_types import Metadata
from .aliases import JSON

__all__ = ["ID", "Metadata", "JSON"]
