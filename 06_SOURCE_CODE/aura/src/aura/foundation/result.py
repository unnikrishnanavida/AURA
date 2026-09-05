"""Result types for AURA.

`Result[T]` is the canonical container for operations that can fail. Engines
return Results instead of raising for expected failures, and raise domain
errors for programmer errors.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any, Generic, TypeVar

from aura.foundation.errors import AuraError

T = TypeVar("T")
U = TypeVar("U")


class Status(StrEnum):
    """Overall execution lifecycle status shared across engines."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Result(Generic[T]):
    """Immutable success/failure container."""

    __slots__ = ("_value", "_error")

    def __init__(self, value: T | None = None, error: AuraError | None = None) -> None:
        if (value is None) == (error is None):
            raise ValueError("Result must have exactly one of value or error")
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        return cls(value=value)

    @classmethod
    def err(cls, error: AuraError) -> Result[T]:
        return cls(error=error)

    @property
    def is_ok(self) -> bool:
        return self._error is None

    @property
    def is_err(self) -> bool:
        return self._error is not None

    def unwrap(self) -> T:
        if self._error is not None:
            raise self._error
        assert self._value is not None
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value if self._error is None and self._value is not None else default

    def map(self, fn: Callable[[T], U]) -> Result[U]:
        if self._error is not None:
            return Result[U](error=self._error)
        assert self._value is not None
        return Result[U](value=fn(self._value))

    @property
    def error(self) -> AuraError | None:
        return self._error

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Success({self._value!r})"
        return f"Failure({self._error!r})"


class Success(Result[T]):
    def __init__(self, value: T) -> None:
        super().__init__(value=value)


class Failure(Result[T]):
    def __init__(self, error: AuraError) -> None:
        super().__init__(error=error)


def ok(value: T) -> Result[T]:
    return Success(value)


def err(error: AuraError) -> Result[Any]:
    return Failure(error)


__all__ = ["Failure", "Result", "Status", "Success", "err", "ok"]