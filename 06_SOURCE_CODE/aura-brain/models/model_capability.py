"""Capability descriptor for models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModelCapability:
    """Describes a capability exposed by a model."""

    name: str
    description: str = ""
    enabled: bool = True
