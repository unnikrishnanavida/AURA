"""API security tests: key lifecycle, rate limiting, request limits, audit trails."""

from __future__ import annotations

import json
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from aura.api.security import ApiKeyIssuer, RateLimiter, check_request_size
from aura.api.server import AuraApiServer, ServerConfig
from aura.security.audit import AuditLog

ADMIN_KEY = "admin-key-at-least-16-char"
SERVICE_KEY = "service-key-at-least-16-char"


def _start(api: AuraApiServer) -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api._httpd = httpd
    return httpd.server_port


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8")
    conn.request("POST", path, body=data, headers={**headers, "Content-Length": str(len(data))})
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    try:
        return response.status, json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return response.status, {}


# -- unit: issuer ---------------------------------------------------------------
def test_api_key_issuer_issue_and_validate() -> None:
    issuer = ApiKeyIssuer(secret="a-secret-that-is-16-plus-chars")
    raw, key_id = issuer.issue()
    assert key_id
    spec = issuer.validate(raw)
    assert spec is not None and spec.key_id == key_id


def test_api_key_issuer_revocation_and_expiry() -> None:
    issuer = ApiKeyIssuer(secret="a-secret-that-is-16-plus-chars")
    raw, key_id = issuer.issue(ttl_seconds=0.01)
    assert issuer.validate(raw) is not None
    issuer.revoke(key_id)
    assert issuer.validate(raw) is None
    time.sleep(0.05)
    raw2, _key_id2 = issuer.issue(ttl_seconds=0.01)
    assert issuer.validate(raw2) is not None
    time.sleep(0.05)
    assert issuer.validate(raw2) is None


def test_api_key_issuer_digest_storage_never_leaks_raw() -> None:
    issuer = ApiKeyIssuer(secret="a-secret-that-is-16-plus-chars")
    raw, key_id = issuer.issue()
    assert raw not in str(issuer._keys[key_id].digest)  # type: ignore[index]


def test_api_key_issuer_requires_long_secret() -> None:
    try:
        ApiKeyIssuer(secret="short")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_rate_limiter_enforces_burst() -> None:
    limiter = RateLimiter(burst=3, per_second=0.1)
    assert all(limiter.allow("1.2.3.4") for _ in range(3))
    assert not limiter.allow("1.2.3.4")
    limiter.reset()
    assert limiter.allow("1.2.3.4") is True


def test_rate_limiter_refills_over_time() -> None:
    limiter = RateLimiter(burst=1, per_second=10.0)
    assert limiter.allow("127.0.0.1")
    assert not limiter.allow("127.0.0.1")
    time.sleep(0.15)
    assert limiter.allow("127.0.0.1")


def test_check_request_size_wall() -> None:
    assert check_request_size(10) is True
    assert check_request_size(2_000_000) is False
    assert check_request_size(-5) is False


# -- integration: server ----------------------------------------------------------
def _secure_server() -> tuple[AuraApiServer, int]:
    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key=SERVICE_KEY,
            admin_key=ADMIN_KEY,
            rate_burst=50,
            rate_per_second=10.0,
            max_request_bytes=1024,
        ),
        audit_log=AuditLog(),
    )
    return api, _start(api)


def test_server_rejects_wrong_key() -> None:
    _api, port = _secure_server()
    status, _ = _post(port, "/v1/reason", {"question": "x"}, token="incorrect-key-12345")
    assert status == 401


def test_server_accepts_valid_key() -> None:
    _api, port = _secure_server()
    status, body = _post(port, "/v1/reason", {"question": "is the api here?"}, token=SERVICE_KEY)
    assert status == 200
    assert "execution_id" in body


def test_server_rejects_oversized_body() -> None:
    _api, port = _secure_server()
    huge = {"question": "x" * 5000}
    status, _ = _post(port, "/v1/reason", huge, token=SERVICE_KEY)
    assert status == 413


def test_server_rate_limits_and_audits() -> None:
    api = AuraApiServer(
        config=ServerConfig(
            host="127.0.0.1",
            port=0,
            api_key=SERVICE_KEY,
            admin_key=ADMIN_KEY,
            rate_burst=2,
            rate_per_second=0.01,
        ),
        audit_log=AuditLog(),
    )
    port = _start(api)
    ok_statuses = 0
    denied = 0
    for _ in range(5):
        status, _ = _post(port, "/v1/reason", {"question": "q"}, token=SERVICE_KEY)
        if status == 200:
            ok_statuses += 1
        elif status == 429:
            denied += 1
    assert ok_statuses == 2
    assert denied >= 1
    assert any(r.action == "rate_limit.deny" for r in api.audit.entries())


def test_server_admin_issue_key() -> None:
    _api, port = _secure_server()
    status, body = _post(port, "/v1/keys", {"ttl_seconds": 60}, token=ADMIN_KEY)
    assert status == 201
    assert "api_key" in body
    assert "key_id" in body
    status2, _ = _post(port, "/v1/reason", {"question": "x"}, token=str(body["api_key"]))
    assert status2 == 200


def test_server_admin_issue_requires_admin() -> None:
    _api, port = _secure_server()
    status, _ = _post(port, "/v1/keys", {"ttl_seconds": 60}, token=SERVICE_KEY)
    assert status == 403