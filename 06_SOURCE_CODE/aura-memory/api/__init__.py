"""Minimal HTTP API for aura-memory using wsgiref (no external deps).

Endpoints:
- GET /health -> 200 OK
- GET /get?key=KEY -> JSON value or 404
- POST /set -> JSON body {"key": ..., "value": ..., "ttl": optional}
- POST /delete -> JSON body {"key": ...}

This module loads the local `persistence` package directly to avoid top-level
package import issues when run from the workspace.
"""

from __future__ import annotations

import importlib.util
import json
import os
from urllib.parse import parse_qs
from wsgiref.util import setup_testing_defaults
from typing import Callable

# load local modules by path
_here = os.path.dirname(__file__)
_package_root = os.path.abspath(os.path.join(_here, ".."))

_monitoring_init = os.path.join(_package_root, "monitoring", "__init__.py")
_monitoring_spec = importlib.util.spec_from_file_location("aura_memory.monitoring", _monitoring_init)
_monitoring = importlib.util.module_from_spec(_monitoring_spec)  # type: ignore[arg-type]
assert _monitoring_spec and _monitoring_spec.loader
_monitoring_spec.loader.exec_module(_monitoring)  # type: ignore[arg-type]

_permissions_init = os.path.join(_package_root, "permissions", "__init__.py")
_permissions_spec = importlib.util.spec_from_file_location("aura_memory.permissions", _permissions_init)
_permissions = importlib.util.module_from_spec(_permissions_spec)  # type: ignore[arg-type]
assert _permissions_spec and _permissions_spec.loader
_permissions_spec.loader.exec_module(_permissions)  # type: ignore[arg-type]

_persistence_init = os.path.join(_package_root, "persistence", "__init__.py")
_persistence_spec = importlib.util.spec_from_file_location("aura_memory.persistence", _persistence_init)
_persistence = importlib.util.module_from_spec(_persistence_spec)  # type: ignore[arg-type]
assert _persistence_spec and _persistence_spec.loader
_persistence_spec.loader.exec_module(_persistence)  # type: ignore[arg-type]

StorageClass = _persistence.InMemoryStorage
_store = StorageClass()

increment = _monitoring.increment
snapshot = _monitoring.snapshot
AuthorizationError = _permissions.AuthorizationError
get_default_permission_store = _permissions.get_default_permission_store
Permissions = get_default_permission_store()


def _json_response(start_response: Callable, status: str, body: dict):
	data = json.dumps(body, default=str).encode("utf-8")
	start_response(status, [("Content-Type", "application/json; charset=utf-8")])
	return [data]


def _authorized(environ, operation: str) -> Optional[str]:
	header = environ.get("HTTP_X_API_KEY") or environ.get("HTTP_AUTHORIZATION")
	if header is None:
		return None
	if header.startswith("Bearer "):
		header = header[len("Bearer ") :]
	try:
		Permissions.authorize(header, operation)
		return header
	except AuthorizationError:
		return None


def app(environ, start_response):
	setup_testing_defaults(environ)
	path = environ.get("PATH_INFO", "/")
	method = environ.get("REQUEST_METHOD", "GET")

	if path == "/health":
		increment("api.requests.health")
		return _json_response(start_response, "200 OK", {"status": "ok"})

	if path == "/get" and method == "GET":
		increment("api.requests.get")
		qs = parse_qs(environ.get("QUERY_STRING", ""))
		key = qs.get("key", [None])[0]
		if not key:
			return _json_response(start_response, "400 Bad Request", {"error": "missing key"})
		if _authorized(environ, "read") is None:
			return _json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
		v = _store.get(key)
		if v is None:
			return _json_response(start_response, "404 Not Found", {"error": "not found"})
		return _json_response(start_response, "200 OK", {"key": key, "value": v})

	if path == "/set" and method in ("POST", "PUT"):
		increment("api.requests.set")
		if _authorized(environ, "write") is None:
			return _json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
		try:
			size = int(environ.get("CONTENT_LENGTH", 0) or 0)
		except Exception:
			size = 0
		body = environ["wsgi.input"].read(size) if size else b""
		try:
			payload = json.loads(body.decode("utf-8") or "{}")
		except Exception:
			return _json_response(start_response, "400 Bad Request", {"error": "invalid json"})
		key = payload.get("key")
		value = payload.get("value")
		ttl = payload.get("ttl")
		if key is None:
			return _json_response(start_response, "400 Bad Request", {"error": "missing key"})
		_store.set(key, value, ttl=ttl)
		return _json_response(start_response, "200 OK", {"key": key})

	if path == "/delete" and method in ("POST", "DELETE"):
		increment("api.requests.delete")
		if _authorized(environ, "delete") is None:
			return _json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
		try:
			size = int(environ.get("CONTENT_LENGTH", 0) or 0)
		except Exception:
			size = 0
		body = environ["wsgi.input"].read(size) if size else b""
		try:
			payload = json.loads(body.decode("utf-8") or "{}")
		except Exception:
			return _json_response(start_response, "400 Bad Request", {"error": "invalid json"})
		key = payload.get("key")
		if key is None:
			return _json_response(start_response, "400 Bad Request", {"error": "missing key"})
		_store.delete(key)
		return _json_response(start_response, "200 OK", {"key": key})

	if path == "/metrics" and method == "GET":
		increment("api.requests.metrics")
		return _json_response(start_response, "200 OK", snapshot())

	return _json_response(start_response, "404 Not Found", {"error": "unknown route"})


__all__ = ["app", "StorageClass"]
