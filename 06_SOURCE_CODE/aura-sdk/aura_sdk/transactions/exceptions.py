"""AURA SDK Transactions exceptions."""


class TransactionError(Exception):
    """Base exception for aura_sdk.transactions."""


class TransactionNotFoundError(TransactionError):
    """Raised when a transactions resource is missing."""


class TransactionValidationError(TransactionError):
    """Raised when a transactions resource fails validation."""


__all__ = [
    "TransactionError",
    "TransactionNotFoundError",
    "TransactionValidationError",
]
