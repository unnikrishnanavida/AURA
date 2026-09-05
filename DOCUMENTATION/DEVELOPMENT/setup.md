# AURA Development Setup

## Requirements

- Python 3.11+ (canonical `aura/` declares `>=3.11`)
- A development virtual environment

## Install the canonical runtime

```sh
cd 06_SOURCE_CODE/aura
python -m pip install -e .[dev]
```

## Run tests for the canonical runtime

```sh
python -m pytest tests -q
```

## Run validation gates

```sh
python -m ruff check src tests scripts
python -m mypy src
python scripts/validate_imports.py
python scripts/security_check.py
python -m build          # produce wheel + sdist
```

## Standalone engines

Each strong engine is independently testable from its own directory:

```sh
cd 06_SOURCE_CODE/aura-agents && python -m pytest tests -q
cd 06_SOURCE_CODE/aura-research && python -m pytest tests -q
cd 06_SOURCE_CODE/aura-security && python -m pytest Tests -q
cd 06_SOURCE_CODE/aura-execution-complete && python -m pytest tests -q
cd 06_SOURCE_CODE/aura-cloud && PYTHONPATH=src python -m pytest tests -q
```

## NOT RUN / environment notes

- Kubernetes deployment validation: not run (no cluster available here).
- External provider SDK integration tests: not run (no provider credentials).
- Some standalone repos have flat layouts; their tests may reference package
  names that are not wired yet (see `STATUS/ecosystem-status.md`).