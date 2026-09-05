"""AURA API service.

A dependency-light HTTP API exposing the platform through stable endpoints
using the standard library HTTP server. Every response carries correlation
and execution ids.

Endpoints:
  GET  /health              liveness
  GET  /ready               readiness
  POST /v1/reason           one reasoning pass
  GET  /v1/replay/{exec}    replay a recorded execution
  GET  /openapi.json        OpenAPI description
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from aura.foundation.errors import AuraError
from aura.foundation.ids import CorrelationId
from aura.observability.logging import StructuredLogger
from aura.sdk.client import Aura


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765


OPENAPI: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {
        "title": "AURA API",
        "version": "0.2.0",
        "description": "Autonomous Universal Reasoning Architecture HTTP API",
    },
    "paths": {
        "/health": {"get": {"summary": "Liveness", "responses": {"200": {"description": "alive"}}}},
        "/ready": {"get": {"summary": "Readiness", "responses": {"200": {"description": "ready"}}}},
        "/v1/reason": {
            "post": {
                "summary": "Run a reasoning pass",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Reasoning result"}},
            }
        },
        "/v1/replay/{execution_id}": {
            "get": {
                "summary": "Replay an execution",
                "parameters": [
                    {
                        "name": "execution_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "Recorded trajectory"}},
            }
        },
    },
}
class AuraApiServer:
    """Wraps the stdlib HTTP server with the AURA SDK."""

    def __init__(self, *, aura: Aura | None = None, config: ServerConfig | None = None) -> None:
        self.aura = aura or Aura()
        self.config = config or ServerConfig()
        self.logger = StructuredLogger("aura.api")

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A002
                return

            def _send(self, status: int, payload: dict[str, Any], correlation: CorrelationId) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Correlation-Id", str(correlation))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _error(
                self,
                status: int,
                message: str,
                correlation: CorrelationId,
                code: str = "api.error",
            ) -> None:
                self._send(status, {"error": {"code": code, "message": message}}, correlation)

            def _read_json(self) -> dict[str, Any] | None:
                length = int(self.headers.get("Content-Length", "0") or 0)
                if length <= 0:
                    return {}
                try:
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                    return data if isinstance(data, dict) else None
                except json.JSONDecodeError:
                    return None

            def do_GET(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if path == "/health":
                    self._send(200, {"status": "ok", "service": "aura-api"}, correlation)
                    return
                if path == "/ready":
                    health = service.aura.health()
                    ready = health["status"] == "ok"
                    self._send(
                        200 if ready else 503,
                        {"status": "ready" if ready else "not_ready", "details": health},
                        correlation,
                    )
                    return
                if path.startswith("/v1/replay/"):
                    execution_id = path.split("/v1/replay/", 1)[1]
                    try:
                        replay = service.aura.replay(execution_id)
                        self._send(200, replay, correlation)
                    except AuraError as exc:
                        self._error(404, exc.message, correlation, exc.code)
                    return
                if path == "/openapi.json":
                    self._send(200, OPENAPI, correlation)
                    return
                self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")

            def do_POST(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if path == "/v1/reason":
                    body = self._read_json()
                    if body is None:
                        self._error(
                            400, "request body must be a JSON object", correlation, "api.invalid_json"
                        )
                        return
                    question = body.get("question")
                    if not isinstance(question, str) or not question.strip():
                        self._error(
                            400,
                            "field 'question' is required and must be a string",
                            correlation,
                            "api.validation",
                        )
                        return
                    facts = body.get("facts", {})
                    if not isinstance(facts, dict):
                        self._error(
                            400,
                            "field 'facts' must be an object mapping to numbers",
                            correlation,
                            "api.validation",
                        )
                        return
                    result = service.aura.reason(question, facts=facts)
                    self._send(200, result, correlation)
                    return
                self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")

        return Handler

    def run(self) -> None:
        server = ThreadingHTTPServer((self.config.host, self.config.port), self._handler())
        self.logger.info("aura-api listening", host=self.config.host, port=str(self.config.port))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("aura-api shutting down")
        finally:
            server.server_close()


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    AuraApiServer(config=ServerConfig(host=host, port=port)).run()


if __name__ == "__main__":
    run_server(host=sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1")

__all__ = ["AuraApiServer", "OPENAPI", "ServerConfig", "run_server"]