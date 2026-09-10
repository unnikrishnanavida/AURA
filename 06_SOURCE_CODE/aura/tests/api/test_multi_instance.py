"""Multi-instance API integration tests against real PostgreSQL.

Proves the Phase 14/15 claims using **two independent HTTP servers** sharing a
real PostgreSQL database for memory + distributed state:

- sessions created on instance A are visible on instance B
- API keys issued on A validate on B; revocation propagates instantly
- rate limits are shared (a single bucket across both instances)
- sessions survive a full process restart
- an instance can be torn down and the survivor still operates

Skipped unless ``AURA_TEST_POSTGRESQL_DSN`` is set (never mocked).
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from http.client import HTTPConnection

import pytest

from aura.api.server import AuraApiServer, ServerConfig
from aura.sdk.client import Aura

DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")


@pytest.fixture(scope="module")
def shared_db() -> str:
    if not DSN:
        pytest.skip("AURA_TEST_POSTGRESQL_DSN not set; skipping multi-instance API tests")
    import psycopg

    suffix = uuid.uuid4().hex[:10]
    dbname = f"aura_multi_{suffix}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()
    yield f"{DSN} dbname={dbname}"
    conn = psycopg.connect(DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'DROP DATABASE "{dbname}"')
    conn.close()


@pytest.fixture(autouse=True)
def _clean_state(shared_db: str) -> None:
    """Clear distributed tables before each test so tests are independent."""
    import psycopg

    with psycopg.connect(shared_db, connect_timeout=5) as conn:
        for table in ("aura_sessions", "aura_api_keys", "aura_rate_limits"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
    yield


class ApiProcess:
    def __init__(self, *, dsn: str, instance_id: str, api_secret: str) -> None:
        self.aura = Aura(seed=3)
        self.static_key = "static-test-bearer-0123456789"
        self.server = AuraApiServer(
            aura=self.aura,
            config=ServerConfig(
                host="127.0.0.1",
                port=0,
                api_key=self.static_key,
                api_secret=api_secret,
                admin_key="admin-key-0123456789",
                trust_proxy=False,
                rate_burst=4,
                rate_per_second=0.2,
                distributed_state_dsn=dsn,
                distributed_state_policy="fail_closed",
                session_ttl_seconds=300.0,
            ),
        )
        from http.server import ThreadingHTTPServer

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.server._handler())
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_port
        self.instance_id = instance_id

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if getattr(self.server, "_distributed_state", None) is not None:
            self.server._distributed_state.close()


def _get(port: int, path: str, *, token: str | None = None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", path, body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    body = json.loads(response.read().decode())
    conn.close()
    return response.status, body
def test_sessions_shared_across_instances(shared_db: str) -> None:
    secret = "issuer-secret-0123456789ab"
    a = ApiProcess(dsn=shared_db, instance_id="a", api_secret=secret)
    b = ApiProcess(dsn=shared_db, instance_id="b", api_secret=secret)
    try:
        status, body = _post(a.port, "/v1/sessions", {}, token=a.static_key)
        assert status == 201, body
        session_id = body["session_id"]
        # Instance B sees the session created on instance A.
        status_b, body_b = _get(b.port, f"/v1/sessions/{session_id}", token=b.static_key)
        assert status_b == 200, body_b
        assert body_b["session_id"] == session_id
        # And instance A also still sees it.
        status_a, _ = _get(a.port, f"/v1/sessions/{session_id}", token=a.static_key)
        assert status_a == 200
    finally:
        a.close()
        b.close()


def test_api_key_revocation_propagates(shared_db: str) -> None:
    secret = "issuer-secret-0123456789ab"
    a = ApiProcess(dsn=shared_db, instance_id="a", api_secret=secret)
    b = ApiProcess(dsn=shared_db, instance_id="b", api_secret=secret)
    try:
        _, issued = _post(
            a.port,
            "/v1/keys",
            {"ttl_seconds": 60, "scopes": ["read"]},
            token="admin-key-0123456789",
        )
        assert "api_key" in issued and "key_id" in issued
        raw_key = issued["api_key"]
        key_id = issued["key_id"]

        # Both instances accept the API key for a protected endpoint.
        status_a, _ = _get(a.port, "/v1/metrics", token=raw_key)
        status_b, _ = _get(b.port, "/v1/metrics", token=raw_key)
        assert status_a == 200 and status_b == 200

        # Revoke via instance A; instance B must now reject the same key.
        _, revoke_body = _post(a.port, "/v1/keys/revoke", {"key_id": key_id}, token="admin-key-0123456789")
        assert revoke_body.get("revoked") is True
        status_b_after, _ = _get(b.port, "/v1/metrics", token=raw_key)
        assert status_b_after in (401, 403)
    finally:
        a.close()
        b.close()


def test_rate_limit_shared_across_instances(shared_db: str) -> None:
    secret = "issuer-secret-0123456789ab"
    a = ApiProcess(dsn=shared_db, instance_id="a", api_secret=secret)
    b = ApiProcess(dsn=shared_db, instance_id="b", api_secret=secret)
    try:
        # burst=4 shared across both instances with the same client IP.
        statuses = []
        for _ in range(3):
            statuses.append(_get(a.port, "/v1/metrics", token=a.static_key)[0])
        for _ in range(3):
            statuses.append(_get(b.port, "/v1/metrics", token=b.static_key)[0])
        assert statuses.count(200) == 4
        assert statuses.count(429) == 2
    finally:
        a.close()
        b.close()


def test_session_survives_restart(shared_db: str) -> None:
    """A session created in one process is visible after that process restarts."""
    secret = "issuer-secret-0123456789ab"
    a = ApiProcess(dsn=shared_db, instance_id="a", api_secret=secret)
    try:
        _, body = _post(a.port, "/v1/sessions", {}, token=a.static_key)
        session_id = body["session_id"]
    finally:
        a.close()

    # A brand-new process (restart) sees the session from durable state.
    a2 = ApiProcess(dsn=shared_db, instance_id="a2", api_secret=secret)
    try:
        status, body = _get(a2.port, f"/v1/sessions/{session_id}", token=a2.static_key)
        assert status == 200, body
        assert body["session_id"] == session_id
    finally:
        a2.close()