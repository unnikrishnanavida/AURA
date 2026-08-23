"""AURA SDK Plugins exceptions."""


class PluginError(Exception):
    """Base exception for aura_sdk.plugins."""


class PluginNotFoundError(PluginError):
    """Raised when a plugins resource is missing."""


class PluginValidationError(PluginError):
    """Raised when a plugins resource fails validation."""


__all__ = [
    "PluginError",
    "PluginNotFoundError",
    "PluginValidationError",
]
