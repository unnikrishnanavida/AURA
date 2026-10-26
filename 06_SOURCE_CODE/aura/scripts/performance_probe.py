"""Phase 43 (G): bounded local performance/operational probe.

Loads the REAL AURA HTTP API (/v1/reason, embedded deterministic provider,
in-memory store) with a bounded synthetic workload: 200 requests across 8
threads. Reports latency percentiles, error count, and the post-run metrics
snapshot. Services are created and destroyed inside this probe only.

Usage: <venv>/python scripts/performance_probe.py
"""

from __future__ import annotations

import contextlib
import json
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura

TOTAL = 200
THREADS = 8
QUESTION = {"question": "is the deployment safe?"}


def worker(port: int, results: list[float], errors: list[str]) -> None:
    for _ in range(TOTAL // THREADS):
        start = time.perf_counter()
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=15)
            conn.request("POST", "/v1/reason", body=json.dumps(QUESTION).encode(),
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            _ = resp.read()
            status = resp.status
            conn.close()
            if status != 200:
                errors.append(f"http {status}")
        except Exception as exc:  # noqa: BLE001 - count as failure
            errors.append(type(exc).__name__)
        results.append((time.perf_counter() - start) * 1000.0)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    i = max(0, min(len(ordered) - 1, int((p / 100.0) * len(ordered))))
    return ordered[i]


def main() -> int:
    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=7),
        config=ServerConfig(host="127.0.0.1", port=0, rate_burst=1000, rate_per_second=500),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())  # noqa: SLF001
    port = httpd.server_address[1]
    httpd.timeout = 20
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        results: list[float] = []
        errors: list[str] = []
        threads = [
            threading.Thread(target=worker, args=(port, results, errors))
            for _ in range(THREADS)
        ]
        started = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - started
        metrics = api.aura.metrics()
        print(f"PERF requests={len(results)} errors={len(errors)} "
              f"elapsed_s={elapsed:.2f} throughput_req_s={len(results)/elapsed:.1f}")
        if results:
            print(f"PERF latency_ms p50={percentile(results, 50):.1f} "
                  f"p95={percentile(results, 95):.1f} max={max(results):.1f}")
        print(f"PERF metrics execution_count={metrics['counters'].get('execution_count', 'n/a')} "
              f"rate_limit_deny={metrics['counters'].get('rate_limit_deny', 0)}")
        return 0 if not errors else 1
    finally:
        httpd.shutdown()
        httpd.server_close()
        with contextlib.suppress(Exception):  # noqa: BLE001 - best-effort close
            api.close()


if __name__ == "__main__":
    raise SystemExit(main())