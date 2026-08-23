"""AURA SDK Client exceptions."""


class ClientError(Exception):
    """Base exception for aura_sdk.client."""


class ClientNotFoundError(ClientError):
    """Raised when a client resource is missing."""


class ClientValidationError(ClientError):
    """Raised when a client resource fails validation."""


__all__ = [
    "ClientError",
    "ClientNotFoundError",
    "ClientValidationError",
]
