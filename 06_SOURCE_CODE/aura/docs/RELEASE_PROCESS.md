# AURA Release Process

Defined, reproducible release procedure covering build, verification, security,
and release artifacts. Every command is real and was executed during the
Phase 17-24 independent verification.

## 1. Release gates (mandatory before tagging)

```bash
# With a reachable PostgreSQL and (optionally) Docker daemon:
AURA_TEST_POSTGRESQL_DSN="host=pg port=5432 dbname=postgres user=... password=..." \
  python 06_SOURCE_CODE/scripts/verify_ecosystem.py
```

All 40 gates must be PASSED. Infrastructure-coupled gates report NOT RUN when
their dependency is unavailable; a release classification must discount those
(see `PRODUCTION_VERIFICATION.md` and the independent report).

## 2. Build artifacts

```bash
rm -rf 06_SOURCE_CODE/aura/dist 06_SOURCE_CODE/aura-sdk/dist
python -m build --wheel --outdir 06_SOURCE_CODE/aura/dist 06_SOURCE_CODE/aura
python -m build --wheel --outdir 06_SOURCE_CODE/aura-sdk/dist 06_SOURCE_CODE/aura-sdk
cd 06_SOURCE_CODE/aura-web && npm run build
```

Verify fresh install of wheels:

```bash
python 06_SOURCE_CODE/evaluation/clean_install_test.py
```

## 3. Security checks

```bash
python -m pip_audit --format json --output 06_SOURCE_CODE/release/security/pip-audit.json
python 06_SOURCE_CODE/release/security/extract_npm_audit.py   # writes npm-audit.json
# Secret scan is part of the release gate (git grep); must find nothing.
```

## 4. SBOM

```bash
# Python
.venv/Scripts/cyclonedx-py.exe environment \
  --pyproject 06_SOURCE_CODE/aura/pyproject.toml \
  --pyproject 06_SOURCE_CODE/aura-sdk/pyproject.toml \
  --output-reproducible --of json \
  -o 06_SOURCE_CODE/release/sbom/aura-python.sbom.json \
  .venv/Scripts/python.exe
# Web
cd 06_SOURCE_CODE/aura-web
npx --yes @cyclonedx/cyclonedx-npm \
  --output-file ../release/sbom/aura-web.sbom.json --output-format JSON
```

## 5. Container

```bash
cd 06_SOURCE_CODE/aura && docker build -t aura:<version> .
python 06_SOURCE_CODE/evaluation/container_verify.py
```

## 6. Tagging + manifest

- Tag the release; record the commit hash.
- Update `06_SOURCE_CODE/release/ARTIFACT_MANIFEST.md` with artifact versions,
  build commands, validation, and checksums.
- Record SBOM tool versions in `release/sbom/README.md`.

## 7. Post-release

- Run `evaluation/production_topology_e2e.py` against the tagged image in a
  staging-like environment.
- Schedule a restore drill (see `docs/BACKUP_AND_RECOVERY.md`) and record its
  result.

## Honesty rules

- NOT RUN gates are never reported as passed.
- Benchmark numbers are laden with environment + workload metadata.
- No fabrications: if a scan or an SBOM did not run, it is documented as such.