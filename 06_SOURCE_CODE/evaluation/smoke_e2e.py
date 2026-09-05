"""End-to-end smoke test: canonical API server + SDK HTTP transport.

Starts a real AuraApiServer on a loopback port, then drives it through the
aura-sdk HTTP transport (auth, reason, remember/recall, research, pipeline).
Run from the repository root:

    python 06_SOURCE_CODE/evaluation/smoke_e2e.py
"""

from __future__ import annotations

import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "aura" / "src"))
sys.path.insert(0, str(ROOT / "aura-sdk"))

TEST_KEY = "smoke-e2e-api-key-123456"


def main() -> int:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.foundation.clock import ManualClock
    from aura.memory.models import MemoryType
    from aura.sdk.client import Aura as CanonicalAura
    from aura_sdk import AuraSDK, SdkConfig
    from aura_sdk.config import TransportMode

    aura = CanonicalAura(clock=ManualClock(0), seed=11)
    api = AuraApiServer(
        aura=aura,
        config=ServerConfig(host="127.0.0.1", port=0, api_key=TEST_KEY, allow_pipeline=True),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_port
    print(f"server on 127.0.0.1:{port}")

    client = AuraSDK(
        config=SdkConfig(
            mode=TransportMode.HTTP,
            endpoint=f"http://127.0.0.1:{port}",
            api_key=TEST_KEY,
            timeout_seconds=15,
        )
    )

    checks: list[tuple[str, bool]] = []

    def check(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(f"{'PASS' if ok else 'FAIL'}  {name}")

    health = client.health()
    check("health", health.get("status") == "ok")

    mid = client.remember("smoke", {"text": "e2e"}, kind="episodic")
    check("remember", bool(mid))
    check("recall", any(e["key"] == "smoke" for e in client.recall("smoke")))

    cid = client.observe("the smoke test passed", predicate=("test",))
    check("observe", bool(cid))

    research = client.research("Did the smoke test pass?", claims=("the smoke test passed",))
    check("research", "findings" in research)

    result = client.reason("2 + 2 == 4?", facts={"math_defined": 0.9})
    print("  answer =", result.get("answer"), "confidence =", result.get("confidence"))
    check("reason", "execution_id" in result)

    metrics = client.metrics()
    check("metrics", isinstance(metrics.get("counters"), dict))

    bad = AuraSDK(
        config=SdkConfig(
            mode=TransportMode.HTTP,
            endpoint=f"http://127.0.0.1:{port}",
            api_key="wrong-key-987654",
        )
    )
    response = bad.execute("reason", {"question": "x"})
    check("auth-rejects-bad-key", response.error is not None and response.error.http_status == 401)

    # The pipeline endpoint executes an inert echo action and audits the
    # security decision; after it runs, the audit log must have entries.
    pipeline = client.execute(
        "pipeline",
        {
            "question": "echo my message safely",
            "goal": "safely echo a message",
            "claims": ("echo is permitted",),
            "tasks": [{"name": "echo", "capability": "tool.echo", "risk": 0.0}],
            "action_inputs": {"echo": {"text": "hello"}},
        },
    )
    check("pipeline-executes", pipeline.ok and pipeline.payload.get("success") is True)

    audit = client.request("audit")
    check("audit-entries", bool(audit.payload.get("entries")))

    httpd.shutdown()
    httpd.server_close()

    passed = sum(1 for _name, ok in checks if ok)
    print(f"\n{passed}/{len(checks)} smoke checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())