"""Abstract interfaces for registry components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class RegistryComponent(ABC):
    """Base interface for registry-backed components."""

    @abstractmethod
    def register(self, item: T) -> None:
        """Register an item."""

    @abstractmethod
    def get(self, name: str) -> T:
        """Retrieve an item by name."""

    @abstractmethod
    def list(self) -> list[T]:
        """List all known items."""


class RegistryStore(ABC, Generic[T]):
    """Interface for registry storage backends."""

    @abstractmethod
    def save(self, item: T) -> None:
        """Persist an item."""

    @abstractmethod
    def load(self, name: str) -> T:
        """Load an item by name."""

    @abstractmethod
    def delete(self, name: str) -> None:
        """Delete an item by name."""

    @abstractmethod
    def all(self) -> list[T]:
        """Return all stored items."""
