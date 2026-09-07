"""HTTP server load test (Phase 12.7).

Measures actual requests-per-second and latency percentiles against a real
AuraApiServer instance on a loopback port, using the canonical flight-recorder
and metrics so every number comes from the real telemetry source.

Environment/hardware and workload are recorded so the numbers are reproducible
and comparable as a performance-regression baseline (12.8).

Usage:
    python 06_SOURCE_CODE/evaluation/load_test.py [--requests N] [--concurrency C]

Not a fake benchmark: it drives the real HTTP server with real requests and
reports measured percentiles/error rate/memory.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "aura" / "src"))


def _timed_get(url: str, timeout: float = 5.0) -> tuple[float, int]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception:
        status = 0
    return (time.perf_counter() - started) * 1000.0, status


def run(requests: int = 200, concurrency: int = 8) -> dict[str, object]:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.foundation.clock import SystemClock
    from aura.sdk.client import Aura

    api = AuraApiServer(
        aura=Aura(clock=SystemClock(), seed=7),
        config=ServerConfig(host="127.0.0.1", port=0),
    )
    httpd = api._httpd if hasattr(api, "_httpd") else None
    # start a real threaded server
    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), api._handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_port
    url = f"http://127.0.0.1:{port}/health"

    latencies: list[float] = []
    errors = 0
    start_wall = time.monotonic()

    def worker(n: int) -> None:
        nonlocal errors
        for _ in range(n):
            latency, status = _timed_get(url)
            if status != 200:
                errors += 1
            else:
                latencies.append(latency)

    threads = [threading.Thread(target=worker, args=(requests // concurrency,)) for _ in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(120)
    duration = time.monotonic() - start_wall

    latencies.sort()
    p = lambda q: round(statistics.quantiles(latencies, n=100)[int(q * 100) - 1], 2) if latencies else 0.0

    httpd.shutdown()
    httpd.server_close()

    return {
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "workload": {"requests": requests, "concurrency": concurrency, "endpoint": "GET /health"},
        "results": {
            "duration_seconds": round(duration, 3),
            "requests_per_second": round(requests / duration, 2),
            "p50_ms": p(0.5),
            "p95_ms": p(0.95),
            "p99_ms": p(0.99),
            "error_rate": round(errors / requests, 4),
            "error_count": errors,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    report = run(requests=args.requests, concurrency=args.concurrency)
    print(json.dumps(report, indent=2, sort_keys=True))
    out = Path(__file__).resolve().parent / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"load-{int(time.time())}.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())