"""AURA SDK Diagnostics exceptions."""


class DiagnosticError(Exception):
    """Base exception for aura_sdk.diagnostics."""


class DiagnosticNotFoundError(DiagnosticError):
    """Raised when a diagnostics resource is missing."""


class DiagnosticValidationError(DiagnosticError):
    """Raised when a diagnostics resource fails validation."""


__all__ = [
    "DiagnosticError",
    "DiagnosticNotFoundError",
    "DiagnosticValidationError",
]
