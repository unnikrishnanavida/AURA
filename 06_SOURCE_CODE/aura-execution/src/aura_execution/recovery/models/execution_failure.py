"""Recovery failure classification model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionFailure:
    """Classified failure attributes used to recommend recovery."""

    error: str
    transient: bool = False
    timeout: bool = False
    policy: bool = False
    resource: bool = False


__all__ = ["ExecutionFailure"]