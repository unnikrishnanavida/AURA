"""AURA SDK Benchmarking exceptions."""


class BenchmarkingError(Exception):
    """Base exception for aura_sdk.benchmarking."""


class BenchmarkingNotFoundError(BenchmarkingError):
    """Raised when a benchmarking resource is missing."""


class BenchmarkingValidationError(BenchmarkingError):
    """Raised when a benchmarking resource fails validation."""


__all__ = [
    "BenchmarkingError",
    "BenchmarkingNotFoundError",
    "BenchmarkingValidationError",
]
