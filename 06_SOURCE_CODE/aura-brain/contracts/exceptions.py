"""
AURA Contracts Exceptions
"""

from __future__ import annotations


class ContractError(Exception):
    """Base contract exception."""


class InvalidContractError(ContractError):
    """Raised when a contract is invalid."""


class ValidationError(ContractError):
    """Raised when validation fails."""


class SerializationError(ContractError):
    """Raised during serialization/deserialization."""


class RoutingError(ContractError):
    """Raised when routing a contract fails."""