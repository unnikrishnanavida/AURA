"""Canonical identifiers for the AURA Agent runtime.

Identifiers are immutable ``str`` subclasses that carry their own prefix so
different domain objects can never be confused. They are simple value objects
with no behavior, kept tiny and dependency-free so they can be imported
everywhere without risk of circular imports.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

__all__ = ["Id", "AgentId", "GoalId", "ActionId", "ExecutionId"]


class Id(str):
    """Base class for namespaced identifiers.

    A subclass declares a ``_prefix``; ``Id.new()`` produces a unique
    identifier and the constructor validates the namespace prefix.
    """

    _prefix: ClassVar[str]

    def __new__(cls, value: str) -> "Id":
        if not isinstance(value, str) or not value:
            raise ValueError(f"{cls.__name__} must be a non-empty string")
        if not value.startswith(cls._prefix):
            raise ValueError(
                f"{cls.__name__} must start with {cls._prefix!r}; got {value!r}"
            )
        return super().__new__(cls, value)

    @classmethod
    def new(cls) -> "Id":
        """Create a new unique identifier of this class."""
        return cls(f"{cls._prefix}{uuid.uuid4().hex}")


class AgentId(Id):
    """Identifies a single agent instance."""

    _prefix = "ag-"


class GoalId(Id):
    """Identifies a goal instance."""

    _prefix = "goal-"


class ActionId(Id):
    """Identifies an actionable unit (action type)."""

    _prefix = "act-"


class ExecutionId(Id):
    """Identifies a single execution (an attempt to run an action)."""

    _prefix = "exe-"


def ensure_execution_id(value: str | ExecutionId) -> ExecutionId:
    """Coerce a raw string to a validated ``ExecutionId``."""
    if isinstance(value, ExecutionId):
        return value
    return ExecutionId(value)