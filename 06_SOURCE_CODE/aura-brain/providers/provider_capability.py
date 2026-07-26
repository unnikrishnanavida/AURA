"""Capability descriptor for providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderCapability:
    """Describes a capability exposed by a provider."""

    name: str
    description: str = ""
    enabled: bool = True
