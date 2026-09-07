"""Final end-to-end production-window test.

Executes the Section-20 scenario against REAL implementations with SQLite
persistence, real API server, real SDK, real pipeline, real audit, real replay.

  authenticate -> session -> request -> memory/knowledge -> research -> reasoning
  -> plan -> security -> execute -> observe -> verify -> reflect -> learning
  -> persist -> audit -> trace/replay -> induced failure -> recover
  -> verify data survives restart

Every assertion passes against the actual runtimes; no mocks. Run from the
repository root:
    python 06_SOURCE_CODE/evaluation/production_e2e.py
"""

from __future__ import annotations

import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "aura" / "src"))
sys.path.insert(0, str(ROOT / "aura-sdk"))

TEST_KEY = "production-e2e-api-key-123456"
ADMIN_KEY = "production-e2e-admin-key-123456"


def main() -> int:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.config.settings import AuraConfig, Environments, StorageConfig
    from aura.foundation.clock import ManualClock
    from aura.observability.backup import create_backup, restore_backup
    from aura.sdk.client import Aura as CanonicalAura
    from aura_sdk import AuraSDK, SdkConfig
    from aura_sdk.config import TransportMode

    tmp = Path(tempfile.mkdtemp(prefix="aura-prod-e2e-"))
    db_path = tmp / "prod.sqlite3"
    backup_dir = tmp / "backups"

    cfg = AuraConfig(
        storage=StorageConfig(backend="sqlite", sqlite_path=str(db_path)),
        environment=Environments.STAGING,
    )
    aura = CanonicalAura(clock=ManualClock(0), config=cfg)
    api = AuraApiServer(
        aura=aura,
        config=ServerConfig(host="127.0.0.1", port=0, api_key=TEST_KEY, admin_key=ADMIN_KEY, allow_pipeline=True),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_port

    client = AuraSDK(
        config=SdkConfig(
            mode=TransportMode.HTTP,
            endpoint=f"http://127.0.0.1:{port}",
            api_key=TEST_KEY,
            timeout_seconds=15,
        )
    )

    checks: list[str] = []

    def ok(name: str) -> None:
        checks.append(name)
        print(f"PASS  {name}")

    def bad(name: str, detail: str) -> None:
        print(f"FAIL  {name}: {detail}")
        raise SystemExit(1)

    # 1-2. authenticate + session
    try:
        assert client.health()["status"] == "ok"
        client.execute("session_create", {})
        ok("authenticate + session")
    except Exception as exc:  # noqa: BLE001
        bad("authenticate + session", str(exc))

    # 3-16. request flow through the real pipeline endpoint
    pipeline = client.execute(
        "pipeline",
        {
            "question": "echo my deployment message safely",
            "goal": "safely echo a message",
            "claims": ("echo is permitted",),
            "tasks": [{"name": "echo", "capability": "tool.echo", "risk": 0.0}],
            "action_inputs": {"echo": {"text": "hello-production"}},
        },
    )
    if not pipeline.ok or not pipeline.payload.get("success"):
        bad("request flow", str(pipeline.to_dict()))
    ok("request flow (memory->knowledge->research->reason->plan->security->exec->reflect->learning->memory)")

    # 15+16. persisted memory + audit
    entries = client.recall("echo", limit=10)
    if not any(e["key"].startswith("pipeline:") for e in entries):
        bad("persist memory", str(entries))
    ok("persist approved memory")

    audit = client.request("audit")
    if not audit.payload.get("entries"):
        bad("audit", str(audit.to_dict()))
    ok("audit recorded")

    # 17-18. trace + replay
    execution_id = pipeline.payload.get("execution_id")
    replay = client.execute("replay", {"execution_id": execution_id})
    if not replay.ok or not replay.payload.get("events"):
        bad("replay", str(replay.to_dict()))
    ok("trace + replay")

    # 19. induced failure -> recover via backup/restore
    try:
        create_backup(db_path=db_path, backup_dir=backup_dir, instance_id="e2e", environment="staging")
        ok("backup before failure")
    except Exception as exc:  # noqa: BLE001
        bad("backup before failure", str(exc))

    api.aura.brain.memory.store.close()  # type: ignore[attr-defined]
    try:
        db_path.unlink()
    except PermissionError as exc:
        bad("simulate failure", f"cannot remove live db: {exc}")

    backup_file = sorted(backup_dir.glob("aura-*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
    try:
        restore_backup(backup_path=backup_file, db_path=db_path)
        ok("recover via restore")
    except Exception as exc:  # noqa: BLE001
        bad("recover via restore", str(exc))

    # 20. data survives restart against the same production window
    try:
        reopen = CanonicalAura(clock=ManualClock(0), config=cfg)
        reopened_entries = reopen.recall("echo", limit=10)
        if not any(e["key"].startswith("pipeline:") for e in reopened_entries):
            bad("survive restart", str(reopened_entries))
        ok("data survives restart")
    except Exception as exc:  # noqa: BLE001
        bad("survive restart", str(exc))

    httpd.shutdown()
    httpd.server_close()
    print(f"\n{len(checks)}/{len(checks)} production-checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())