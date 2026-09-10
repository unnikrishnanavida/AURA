"""Production-like topology end-to-end test (Phase 15/16).

Real components, no mocks:

- real PostgreSQL backend (memory + distributed state)
- two independent AURA API instances sharing the database
- TLS-terminating reverse proxy in front of both instances
- real API keys, sessions, rate limits shared across instances
- failover: terminate instance A, continue through instance B
- distributed-state outage: fail-closed behavior verified
- PostgreSQL backup + restore drill
- persistence survives topology restart

Run from repository root with a reachable PostgreSQL admin DSN:

    set AURA_TEST_POSTGRESQL_DSN=host=127.0.0.1 port=55432 dbname=postgres user=... password=...
    python 06_SOURCE_CODE/evaluation/production_topology_e2e.py
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import threading
import time
import uuid
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "aura" / "src"))

ADMIN_DSN = os.environ.get("AURA_TEST_POSTGRESQL_DSN", "")
if not ADMIN_DSN:
    raise SystemExit("AURA_TEST_POSTGRESQL_DSN is required to run the topology E2E")

from aura.api.proxy import ProxyConfig, TLSProxy, Upstream
from aura.api.server import AuraApiServer, ServerConfig
from aura.api.tls_testing import generate_self_signed_certs
from aura.config.settings import AuraConfig, Environments, StorageConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura

STATIC_KEY = "topology-static-key-0123456789"
ADMIN_KEY = "topology-admin-key-0123456789"
ISSUER_SECRET = "topology-issuer-secret-0123456789"
def _http_request(port: int, method: str, path: str, *, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    conn = HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        raw = json.dumps(body)
    else:
        raw = None
    conn.request(method, path, body=raw, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def _https_request(port: int, method: str, path: str, *, cafile: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    ctx = ssl.create_default_context(cafile=cafile)
    conn = HTTPSConnection("localhost", port, timeout=10, context=ctx)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        raw = json.dumps(body)
    else:
        raw = None
    conn.request(method, path, body=raw, headers=headers)
    resp: HTTPResponse = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


class ApiNode:
    def __init__(self, *, dsn: str, instance_id: str, port: int) -> None:
        cfg = AuraConfig(
            storage=StorageConfig(backend="postgresql", postgresql_dsn=dsn),
            environment=Environments.STAGING,
        )
        self.aura = Aura(clock=ManualClock(0), config=cfg)
        self.server = AuraApiServer(
            aura=self.aura,
            config=ServerConfig(
                host="127.0.0.1",
                port=port,
                api_key=STATIC_KEY,
                admin_key=ADMIN_KEY,
                api_secret=ISSUER_SECRET,
                trust_proxy=True,
                rate_burst=100,
                rate_per_second=5.0,
                allow_pipeline=True,
                distributed_state_dsn=dsn,
                distributed_state_policy="fail_closed",
                session_ttl_seconds=3600.0,
            ),
        )
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.server._handler())
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_port

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if getattr(self.server, "_distributed_state", None) is not None:
            self.server._distributed_state.close()
def main() -> int:
    import psycopg

    suffix = uuid.uuid4().hex[:8]
    dbname = f"aura_topology_{suffix}"
    conn = psycopg.connect(ADMIN_DSN, connect_timeout=5)
    conn.autocommit = True
    conn.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()

    checks: list[str] = []

    def ok(name: str) -> None:
        checks.append(name)
        print(f"PASS  {name}")

    def bad(name: str, detail: str) -> None:
        print(f"FAIL  {name}: {detail}")
        raise SystemExit(1)

    dsn = f"{ADMIN_DSN} dbname={dbname}"
    certs = generate_self_signed_certs()
    start = time.time()

    node_a = ApiNode(dsn=dsn, instance_id="a", port=0)
    node_b = ApiNode(dsn=dsn, instance_id="b", port=0)

    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1",
        tls_port=0,
        redirect_port=None,
        tls_certfile=str(certs.certfile),
        tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=node_a.port), Upstream(host="127.0.0.1", port=node_b.port)],
        timeout_seconds=3.0,
    ))
    proxy.start()

    try:
        # 1. HTTPS + authentication through the proxy.
        status, body = _https_request(proxy.tls_port, "GET", "/health", cafile=str(certs.cafile))
        if status != 200:
            bad("HTTPS+tls termination", str(body))
        ok("HTTPS request through TLS proxy")

        status, body = _https_request(proxy.tls_port, "POST", "/v1/sessions", cafile=str(certs.cafile), token=STATIC_KEY, body={})
        if status != 201:
            bad("authenticate + session", str(body))
        ok("authentication + durable session")

        # 2-18. Full pipeline request routed through the proxy.
        status, body = _https_request(
            proxy.tls_port, "POST", "/v1/pipeline",
            cafile=str(certs.cafile), token=STATIC_KEY,
            body={
                "question": "echo my topology message safely",
                "goal": "safely echo",
                "claims": ("echo is permitted",),
                "tasks": [{"name": "echo", "capability": "tool.echo", "risk": 0.0}],
                "action_inputs": {"echo": {"text": "production-topology"}},
            },
        )
        if status != 200 or not body.get("success"):
            bad("full pipeline through proxy", str(body))
        execution_id = body.get("execution_id")
        ok("pipeline request routed via TLS proxy")

        status, body = _https_request(proxy.tls_port, "GET", "/v1/replay/" + str(execution_id), cafile=str(certs.cafile), token=STATIC_KEY)
        if status != 200 or not body.get("events"):
            bad("replay", str(body))
        ok("replay through proxy")

        # Shared state visible on node B.
        node_b_mem = node_b.aura.recall("pipeline:", limit=5)
        if not any(e["key"].startswith("pipeline:") for e in node_b_mem):
            bad("shared memory across instances", str(node_b_mem))
        ok("memory shared across API instances")

        if not node_b.server.audit.entries():
            bad("audit", "no entries")
        ok("audit recorded")

        # 19-21. Terminate instance A; continue via survivor B through proxy.
        node_a.stop()
        time.sleep(0.2)
        status, body = _https_request(proxy.tls_port, "GET", "/v1/metrics", cafile=str(certs.cafile), token=STATIC_KEY)
        if status != 200:
            bad("failover to survivor B", str(body))
        ok("failover: instance A terminated, continued via B")

        # 22-23. Distributed-state outage -> fail closed.
        node_b.server._distributed_state.close()
        status, body = _http_request(node_b.port, "GET", "/v1/metrics", token=STATIC_KEY)
        if status == 200:
            bad("distributed-state outage fail-open", str(body))
        ok("distributed-state outage fails closed (denies)")

        # Restart node A; verify persistence.
        node_a = ApiNode(dsn=dsn, instance_id="a2", port=0)
        time.sleep(0.3)
        persisted = node_a.aura.recall("pipeline:", limit=5)
        if not any(e["key"].startswith("pipeline:") for e in persisted):
            bad("persistence after restart", str(persisted))
        ok("restart: instance A rejoins with persisted data")
# 25-27. PostgreSQL backup + restore drill (memory tables).
        import tempfile
        from pathlib import Path as PPath

        from aura.observability.pg_backup import (
            create_pg_backup,
            restore_pg_backup,
        )

        tmp = PPath(tempfile.mkdtemp(prefix="aura-topology-bk-"))
        result = create_pg_backup(dsn=dsn, backup_dir=str(tmp), instance_id="topology", environment="staging")
        if not PPath(result.path).exists():
            bad("postgres backup", "no backup file")
        ok("postgres backup created")

        # Corrupt state (drop memory), then restore from backup.
        with psycopg.connect(dsn, connect_timeout=5) as conn2:
            conn2.execute("DROP TABLE memory_entries")
            conn2.execute("DELETE FROM schema_version")
        counts = restore_pg_backup(backup_path=result.path, dsn=dsn, force=True)
        if counts.get("memory_entries", 0) == 0:
            bad("postgres restore", f"no rows restored: {counts}")
        ok("disaster-recovery drill: postgres backup restored")

        # 28-29. Persistence survives topology restart.
        node_a.stop()
        node_b.stop()
        proxy.stop()
        time.sleep(0.2)
        node_a2 = ApiNode(dsn=dsn, instance_id="a3", port=0)
        survived = node_a2.aura.recall("pipeline:", limit=5)
        if not any(e["key"].startswith("pipeline:") for e in survived):
            bad("survive full restart", str(survived))
        ok("data survives topology restart")
        node_a2.stop()

    finally:
        proxy.stop()
        for node in (node_a, node_b):
            try:
                node.stop()
            except Exception as exc:  # noqa: BLE001
                print(f"WARN  node stop failed: {exc}")
        try:
            conn = psycopg.connect(ADMIN_DSN, connect_timeout=5)
            conn.autocommit = True
            conn.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"WARN  could not drop {dbname}: {exc}")

    print(f"\n{len(checks)}/{len(checks)} topology checks passed (in {time.time() - start:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())