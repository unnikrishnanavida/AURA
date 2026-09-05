"""SDK versioning.

The SDK supports a bounded window of remote API versions. When the remote
server reports a version outside that window the client lifts
``SdkConfigurationError`` rather than guessing at an incompatible contract.
"""

from __future__ import annotations

__version__ = "1.0.0"

SDK_API_VERSION = "0.2"

# Minimum server API version this SDK can talk to. Bump only with a
# coordinated server change.
MIN_SERVER_API_VERSION = "0.2"
MAX_SERVER_API_VERSION = "1.0"


__all__ = [
    "MAX_SERVER_API_VERSION",
    "MIN_SERVER_API_VERSION",
    "SDK_API_VERSION",
    "__version__",
]