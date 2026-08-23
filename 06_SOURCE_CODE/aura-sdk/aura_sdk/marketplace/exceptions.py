"""AURA SDK Marketplace exceptions."""


class MarketplaceError(Exception):
    """Base exception for aura_sdk.marketplace."""


class MarketplaceNotFoundError(MarketplaceError):
    """Raised when a marketplace resource is missing."""


class MarketplaceValidationError(MarketplaceError):
    """Raised when a marketplace resource fails validation."""


__all__ = [
    "MarketplaceError",
    "MarketplaceNotFoundError",
    "MarketplaceValidationError",
]
