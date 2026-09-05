"""AURA API package — thin HTTP service.

Routes contain no domain logic; they validate requests, dispatch to the
platform SDK, and return structured responses/errors with correlation IDs.
"""

from __future__ import annotations

from aura.api.server import AuraApiServer, ServerConfig, run_server

__all__ = ["AuraApiServer", "ServerConfig", "run_server"]