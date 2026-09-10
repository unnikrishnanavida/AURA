"""Reproducible container deployment verification (Phase 18).

Builds the AURA image and exercises the full container lifecycle:

    BUILD -> START -> HEALTH -> READY -> AUTHENTICATE -> REQUEST ->
    PERSIST -> RESTART -> VERIFY DATA

Also verifies the two-instance compose topology (PostgreSQL + shared memory).
Requires a running Docker daemon. Run from the repository root:

    python 06_SOURCE_CODE/evaluation/container_verify.py [--skip-compose]

Exit 0 = all lifecycle checks passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AURA_REPO = ROOT / "aura"
IMAGE = "aura-verify:0.2.0"
CONTAINER = "aura-verify-run"
HOST_PORT = 18765
API_KEY = "container-verify-key-0123456789"


def _run(cmd: list[str], *, timeout: int = 600, cwd: Path | None = None) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout)


def _check(step: str, result: subprocess.CompletedProcess) -> None:
    if result.returncode != 0:
        print(f"[FAIL] {step}: {result.stderr[-1500:] or result.stdout[-1500:]}")
        raise SystemExit(f"container verification failed at: {step}")
    print(f"[ok] {step}")


def _http(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    url = f"http://127.0.0.1:{HOST_PORT}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-compose", action="store_true")
    args = parser.parse_args()

    probes: list[tuple[str, bool]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        probes.append((name, ok))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))

    # 1. BUILD
    result = _run(["docker", "build", "-t", IMAGE, "."], cwd=AURA_REPO)
    check("docker build", result.returncode == 0, result.stderr[-300:])

    # 2. START with sqlite persistence in a named volume
    _run(["docker", "rm", "-f", CONTAINER])
    _run(["docker", "volume", "rm", "aura-verify-data", "-f"])
    run = _run([
        "docker", "run", "-d", "--name", CONTAINER,
        "-e", "AURA_ENVIRONMENT=staging",
        "-e", "AURA_STORAGE_BACKEND=sqlite",
        "-e", "AURA_STORAGE_SQLITE_PATH=/data/aura.sqlite3",
        "-e", f"AURA_API_KEY={API_KEY}",
        "-e", "AURA_API_ALLOW_PIPELINE=1",
        "-v", "aura-verify-data:/data",
        "-p", f"{HOST_PORT}:8765",
        IMAGE,
    ])
    check("docker start", run.returncode == 0, run.stderr[-300:])

    # Wait for readiness
    ready = False
    for _ in range(20):
        time.sleep(3)
        try:
            _, body = _http("GET", "/ready")
            if body.get("status") == "ready":
                ready = True
                break
        except Exception:
            continue
    check("ready", ready)

    # 3. AUTHENTICATE + REQUEST (pipeline)
    status, body = _http("POST", "/v1/pipeline", body={
        "question": "container verify echo",
        "goal": "safely echo",
        "claims": ("echo is permitted",),
        "tasks": [{"name": "echo", "capability": "tool.echo", "risk": 0.0}],
        "action_inputs": {"echo": {"text": "container-persist"}},
    }, token=API_KEY)
    check("authenticated pipeline", status == 200 and body.get("success"), str(body))

    # 4. PERSIST -> RESTART -> VERIFY
    _run(["docker", "restart", CONTAINER])
    time.sleep(8)
    spec_status, health = _http("GET", "/health")
    check("restart health", spec_status == 200 and health.get("status") == "ok", str(health)[:200])
    entries = health.get("engines", {}).get("memory", {}).get("entries", 0)
    check("data survives restart", entries >= 1, f"entries={entries}")

    # Cleanup single container
    _run(["docker", "rm", "-f", CONTAINER])
    _run(["docker", "volume", "rm", "aura-verify-data", "-f"])

    # 5. Compose topology (two instances + PostgreSQL)
    if not args.skip_compose:
        compose = AURA_REPO / "compose.postgres.yaml"
        result = _run(["docker", "compose", "-f", str(compose), "up", "-d", "--build"])
        check("compose up (postgres + 2 api)", result.returncode == 0, result.stderr[-300:])
        time.sleep(15)
        ps = _run(["docker", "ps", "--filter", "name=aura", "--format", "{{.Names}}:{{.Status}}"])
        healthy = sum(1 for line in ps.stdout.splitlines() if "healthy" in line)
        check("compose instances healthy", healthy >= 3, ps.stdout)
        result = _run(["docker", "compose", "-f", str(compose), "down"])
        check("compose down", result.returncode == 0, result.stderr[-200:])

    passed = sum(1 for _, ok in probes if ok)
    print(f"\nCONTAINER VERIFICATION: {passed}/{len(probes)}")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())