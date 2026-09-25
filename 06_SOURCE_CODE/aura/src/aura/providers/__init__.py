"""Model provider abstractions.

AURA is provider-independent. Capabilities are described by
:class:`ProviderProfile`; the ONE :class:`ProviderRegistry` holds profiles and
runtime instances; :class:`~aura.providers.manager.ProviderManager` is the
canonical policy-enforcing dispatch boundary through which reasoning can consult
a generation/synthesis provider. The embedded provider runs deterministic local
reasoning with zero external dependencies; remote adapters are unit-tested but
require operator-supplied credentials for live use.
"""

from __future__ import annotations

from aura.providers.base import (
    Provider,
    ProviderPolicy,
    ProviderProfile,
    ProviderRegistry,
    ProviderUsage,
)
from aura.providers.embedded import EmbeddedReasoningProvider
from aura.providers.errors import (
    MalformedProviderResponse,
    ProviderError,
    ProviderPolicyError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from aura.providers.manager import ProviderManager, build_provider_manager
from aura.providers.remote import HttpChatProviderAdapter

__all__ = [
    "EmbeddedReasoningProvider",
    "HttpChatProviderAdapter",
    "MalformedProviderResponse",
    "Provider",
    "ProviderError",
    "ProviderManager",
    "ProviderPolicy",
    "ProviderPolicyError",
    "ProviderProfile",
    "ProviderRegistry",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "ProviderUsage",
    "build_provider_manager",
]