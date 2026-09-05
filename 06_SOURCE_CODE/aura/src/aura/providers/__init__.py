"""Model provider abstractions.

AURA is provider-independent. Reasoning/embedding/planning capabilities are
described by :class:`ProviderProfile`; providers are matched by capability,
latency, cost, reliability, and privacy requirements. The embedded provider
runs deterministic local reasoning with zero external dependencies.
"""

from __future__ import annotations

from aura.providers.base import ProviderProfile, ProviderRegistry
from aura.providers.embedded import EmbeddedReasoningProvider

__all__ = ["EmbeddedReasoningProvider", "ProviderProfile", "ProviderRegistry"]