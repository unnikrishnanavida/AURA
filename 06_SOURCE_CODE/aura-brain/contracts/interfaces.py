"""
AURA Contracts Interfaces
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Contract(ABC):
    """Base interface for all contracts."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Contract name."""


class Serializable(ABC):
    """Marks a serializable object."""

    @abstractmethod
    def serialize(self) -> str:
        """Serialize object."""


class Validatable(ABC):
    """Marks a validatable object."""

    @abstractmethod
    def validate(self) -> bool:
        """Validate object."""