"""Strongly typed AURA configuration.

One authoritative configuration stack: defaults -> config file -> environment.
Settings are validated at load time; secrets are never serialized or logged.
"""

from __future__ import annotations

from aura.config.loader import ConfigLoader, load_settings, validate_environment
from aura.config.settings import (
    AuraConfig,
    BudgetLimits,
    ConfigSchemaVersion,
    EngineConfig,
    Environments,
    LoggingConfig,
)

__all__ = [
    "AuraConfig",
    "BudgetLimits",
    "ConfigLoader",
    "ConfigSchemaVersion",
    "EngineConfig",
    "Environments",
    "LoggingConfig",
    "load_settings",
    "validate_environment",
]