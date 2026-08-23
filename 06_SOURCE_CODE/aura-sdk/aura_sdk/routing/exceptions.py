"""AURA SDK Routing exceptions."""


class RoutingError(Exception):
    """Base exception for aura_sdk.routing."""


class RoutingNotFoundError(RoutingError):
    """Raised when a routing resource is missing."""


class RoutingValidationError(RoutingError):
    """Raised when a routing resource fails validation."""


__all__ = [
    "RoutingError",
    "RoutingNotFoundError",
    "RoutingValidationError",
]
