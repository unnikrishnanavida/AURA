"""Validation helpers for the gateway subsystem."""

from __future__ import annotations

import json
from typing import Any

from .exceptions import GatewayError


class GatewayValidator:
    """Validate gateway requests and configuration payloads."""

    def validate(self, value: Any) -> None:
        """Validate the supplied value."""
        if value is None:
            raise GatewayError("Request payload cannot be None")
        if isinstance(value, str):
            try:
                json.loads(value)
            except Exception as exc:
                raise GatewayError("Invalid JSON payload") from exc
        elif not isinstance(value, dict):
            raise GatewayError("Request payload must be a JSON object or string.")

    def validate_route(self, route: str) -> None:
        """Validate route names."""
        if not route or not route.strip():
            raise GatewayError("Route cannot be empty")

    def validate_request(self, request: dict[str, Any]) -> None:
        """Validate gateway request structure."""
        if not isinstance(request, dict):
            raise GatewayError("Request must be a dictionary.")
        if "route" not in request or not isinstance(request["route"], str) or not request["route"].strip():
            raise GatewayError("Request must include a non-empty route field.")
        if "payload" not in request:
            raise GatewayError("Request must include a payload field.")
