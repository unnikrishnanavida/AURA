"""AURA SDK Simulation exceptions."""


class SimulationError(Exception):
    """Base exception for aura_sdk.simulation."""


class SimulationNotFoundError(SimulationError):
    """Raised when a simulation resource is missing."""


class SimulationValidationError(SimulationError):
    """Raised when a simulation resource fails validation."""


__all__ = [
    "SimulationError",
    "SimulationNotFoundError",
    "SimulationValidationError",
]
