"""AURA integration SDK.

The developer SDK around the canonical AURA runtime. Import the public
surface:

    from aura_sdk import AuraSDK, SdkConfig

    client = AuraSDK(config=SdkConfig())  # deterministic local mode
    result = client.reason("is the system healthy?", facts={"ok": 0.9})

Submodules are intentionally split: ``client`` (facade), ``transport`` (local
and HTTP backends), ``authentication``, ``middleware``, ``retry``, ``events``,
``sessions``, ``models``, ``config``, ``errors``, and ``_version``.
"""

from __future__ import annotations

from ._version import SDK_API_VERSION, __version__
from .authentication import AnonymousAuthenticator, ApiKeyAuthenticator, Authenticator
from .client import OPERATIONS, AuraSDK
from .config import DEFAULT_ENDPOINT, RetryConfig, SdkConfig, TransportMode
from .errors import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    SdkConfigurationError,
    SdkError,
    SdkRetryExhaustedError,
    SdkTimeoutError,
    SdkValidationError,
    TransportError,
)
from .events import EventBus, SdkEvent
from .models import SdkRequest, SdkResponse
from .sessions import Session, SessionManager
from .transport import HttpTransport, LocalTransport, Transport

__all__ = [
    "ANONYMOUS",
    "AuraSDK",
    "Authenticator",
    "ApiKeyAuthenticator",
    "AnonymousAuthenticator",
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "DEFAULT_ENDPOINT",
    "EventBus",
    "HttpTransport",
    "LocalTransport",
    "OPERATIONS",
    "RetryConfig",
    "SDK_API_VERSION",
    "SdkConfig",
    "SdkConfigurationError",
    "SdkError",
    "SdkEvent",
    "SdkRequest",
    "SdkResponse",
    "SdkRetryExhaustedError",
    "SdkTimeoutError",
    "SdkValidationError",
    "Session",
    "SessionManager",
    "Transport",
    "TransportError",
    "TransportMode",
    "__version__",
]

# Sentinel describing an anonymous client (no credentials needed).
ANONYMOUS = "anonymous"