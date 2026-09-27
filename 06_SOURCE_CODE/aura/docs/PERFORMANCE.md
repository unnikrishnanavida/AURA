# AURA Performance Baseline (local)

Honest single-machine numbers captured 2026-09-25 by
`scripts/benchmark_phase35.py` (in-process canonical paths, Python 3.14,
Windows, E: NVMe). **This is a LOCAL baseline, not a production load test.**

| Path | ms/call | ops/s |
|------|---------|-------|
| `brain.reason` (deterministic, socrates rule set) | ~0.17 | ~5,900 |
| `brain.reason` + synthesis provider (in-process adapter) | ~0.18 | ~5,600 |
| memory write (in-memory store) | ~0.005 | ~188,000 |

Note: provider calls go to an in-process fake in this baseline; real network
provider latency must be re-measured with the configured endpoint.

## What this records and what it does not

- Records: deterministic reasoning and provider-boundary overhead, memory-write
  throughput on this machine.
- Does NOT record: HTTP-layer throughput, multi-instance contention, real
  provider network latency, PG-bound writes, soak/load under failure. Those
  require a staging environment and are **NOT VERIFIED** here.

## Guidance

- Profile before optimizing (rule: never trade security/correctness for
  benchmarks). The reasoning path is already sub-millisecond locally; the
  obvious scaling levers are storage backends and provider latency, not the
  engine internals.