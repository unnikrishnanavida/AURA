"""AURA SDK Middleware exceptions."""


class MiddlewareError(Exception):
    """Base exception for aura_sdk.middleware."""


class MiddlewareNotFoundError(MiddlewareError):
    """Raised when a middleware resource is missing."""


class MiddlewareValidationError(MiddlewareError):
    """Raised when a middleware resource fails validation."""


__all__ = [
    "MiddlewareError",
    "MiddlewareNotFoundError",
    "MiddlewareValidationError",
]
