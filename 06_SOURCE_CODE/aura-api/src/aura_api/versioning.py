"""API versioning for aura-api.

Resolves a requested version (from header or path prefix) against supported
versions, defaulting to the newest supported version and rejecting unknown
versions with a structured 400.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura_api.core.errors import ValidationError


@dataclass
class VersionRegistry:
    """Registry of supported API versions."""

    supported: set[str] = field(default_factory=lambda: {"v1", "v2"})
    default: str = "v1"

    def resolve(self, requested: str | None, *, from_path: str = "") -> str:
        candidate = requested or ""
        if from_path:
            # /v1/... -> v1
            parts = from_path.strip("/").split("/")
            if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
                candidate = parts[0]
        if not candidate:
            return self.default
        if candidate not in self.supported:
            raise ValidationError(
                f"unsupported API version {candidate!r}; supported: {sorted(self.supported)}",
                code="api.unsupported_version",
            )
        return candidate


__all__ = ["VersionRegistry"]