"""AURA SDK Sandbox exceptions."""


class SandboxError(Exception):
    """Base exception for aura_sdk.sandbox."""


class SandboxNotFoundError(SandboxError):
    """Raised when a sandbox resource is missing."""


class SandboxValidationError(SandboxError):
    """Raised when a sandbox resource fails validation."""


__all__ = [
    "SandboxError",
    "SandboxNotFoundError",
    "SandboxValidationError",
]
