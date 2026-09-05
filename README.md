# AURA — Autonomous Universal Reasoning Architecture

AURA is **intelligence infrastructure**: a coherent platform for reasoning,
learning, memory, planning, agents, reflection, knowledge, execution, safety,
replay, provenance, observability, API exposure, and SDK integration.

## What is in this repository

| Path | Purpose |
| ---- | ------- |
| `06_SOURCE_CODE/aura` | **The integrated AURA platform** — the authoritative, tested, installable package (`pip install .[dev]`) |
| `01_FOUNDATION` | Architecture documents, ADRs, charters, standards |
| `02_KNOWLEDGE` | Knowledge base artifacts |
| `06_SOURCE_CODE/aura-*` | Earlier engine scaffolds (see below) |
| `07_SECURITY` / `08_INFRASTRUCTURE` / `10_DATA` / `11_MODELS` | Security, infrastructure, data, and model area documentation |
| `12_DESIGN` / `13_MANAGEMENT` / `14_RELEASES` | Design, management, and release records |
| `TOOLS` | Repository tooling and audit scanners |

## All-in-one quick start

```python
from aura import Aura

aura = Aura(seed=42)
result = aura.reason("flight_approved", facts={"sky_clear": 1.0, "wind_low": 0.8})
print(result["answer"], result["confidence"], result["uncertainty"])
```

Runnable examples live in `06_SOURCE_CODE/aura/examples/`.

## About the earlier engine scaffolds

`06_SOURCE_CODE/aura-memory`, `aura-learning`, `aura-brain`, `aura-reasoning`
(duplicate trees), `aura-planning`, `aura-execution`, and `aura-core` are
**earlier scaffold generations**. The audit found that large portions were
auto-generated and syntactically broken (for example, more than 5,000 files in
`aura-memory` failed compilation). The consolidated, tested implementation is
the single `aura` package; the scaffolds are retained as historical source
areas for reference and are **not** part of the supported public surface.

## Quality gates (run from `06_SOURCE_CODE/aura`)

```bash
python -m ruff check src tests
python -m mypy src
python -m pytest tests
python scripts/security_check.py
python scripts/validate_imports.py
```

## Deployment

`06_SOURCE_CODE/aura/Dockerfile`, `compose.yaml`, and
`.github/workflows/ci.yml` provide container build, local stack, and CI/CD.

## Documentation

- `06_SOURCE_CODE/aura/README.md` — package documentation
- `06_SOURCE_CODE/aura/docs/architecture.md` — engine map and execution flow
- `06_SOURCE_CODE/aura/SECURITY.md` — security model
- `06_SOURCE_CODE/aura/CHANGELOG.md` — release history
