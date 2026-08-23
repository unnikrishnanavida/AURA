"""Typed runtime configuration with environment-aware profiles.

Configuration is strongly typed, validated at startup, and has no hardcoded
secrets. Three profiles exist: ``development`` (permissive, noisy),
``production`` (strict, quiet), and ``research`` (experimental, bounded).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from aura_agent.contracts.errors import ConfigurationError

__all__ = ["RuntimeSettings", "load_settings", "Profile"]


class Profile:
    """Well-known configuration profiles."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    RESEARCH = "research"


@dataclass(frozen=True)
class AgentSettings:
    """Agent-level runtime settings."""

    autonomy_mode: str = "SUPERVISED"
    max_loop_iterations: int = 20
    max_retries_per_step: int = 2
    review_uncovered_risk: float = 0.5
    log_level: str = "INFO"


@dataclass(frozen=True)
class RuntimeSettings:
    """Typed runtime configuration bag."""

    profile: str = Profile.DEVELOPMENT
    agent: AgentSettings = field(default_factory=AgentSettings)
    timeout_s: float = 30.0
    event_store_path: str | None = None
    max_iters: int = 20


def _from_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip() or default


def load_settings(profile: str | None = None) -> RuntimeSettings:
    """Load settings, applying environment overrides and validating types.

    Raises:
        ConfigurationError: the resolved configuration is invalid.
    """
    chosen = profile or _from_env("AURA_AGENT_PROFILE", Profile.DEVELOPMENT)
    if chosen not in (Profile.DEVELOPMENT, Profile.PRODUCTION, Profile.RESEARCH):
        raise ConfigurationError(f"unknown AURA Agent profile {chosen!r}")

    autonomy = _from_env("AURA_AGENT_AUTONOMY", "SUPERVISED")
    if autonomy not in {"MANUAL", "ASSISTED", "SUPERVISED", "AUTONOMOUS"}:
        raise ConfigurationError(
            f"invalid autonomous mode {autonomy!r}; expected MANUAL/ASSISTED/SUPERVISED/AUTONOMOUS"
        )

    try:
        max_iters = int(_from_env("AURA_AGENT_MAX_ITERATIONS", "20"))
        max_retries = int(_from_env("AURA_AGENT_MAX_RETRIES", "2"))
    except ValueError as exc:
        raise ConfigurationError("AURA_AGENT_MAX_ITERATIONS/MAX_RETRIES must be integers") from exc

    if max_iters < 1 or max_retries < 0:
        raise ConfigurationError("iteration/retry counts must be non-negative")

    profile_defaults = {
        Profile.DEVELOPMENT: "INFO",
        Profile.PRODUCTION: "WARNING",
        Profile.RESEARCH: "DEBUG",
    }

    settings = RuntimeSettings(
        profile=chosen,
        agent=AgentSettings(
            autonomy_mode=autonomy,
            max_loop_iterations=max_iters,
            max_retries_per_step=max_retries,
            log_level=(
                _from_env("AURA_AGENT_LOG_LEVEL") or profile_defaults[chosen]
            ),
        ),
        timeout_s=float(_from_env("AURA_AGENT_TIMEOUT_S", "30")),
        max_iters=max_iters,
    )
    return settings