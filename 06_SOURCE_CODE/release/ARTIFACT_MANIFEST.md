# AURA Release Artifact Manifest (Phases 17-24 independent verification)

Real artifacts built, installed, and smoke-tested from the current repository.
Nothing is published externally; these are release candidates.

| Artifact | Version | Build command | Validation |
| -------- | ------- | ------------- | ---------- |
| `aura-0.2.0-py3-none-any.whl` | 0.2.0 | `python -m build --wheel` | fresh-venv install + import + SDK local-mode smoke |
| `aura_sdk-1.0.0-py3-none-any.whl` | 1.0.0 | `python -m build --wheel` | fresh-venv install + import + local-mode health via SDK |
| `aura-web` `dist/` | (web) | `npm run build` | `npm test` + `npm run build` + `npm run lint` + `npm audit` (0 vulns) |
| docker image `aura-verify:0.2.0` | 0.2.0 | `docker build -t aura-verify:0.2.0 .` | container_verify.py 9/9: build→start→health→auth→pipeline→persist→restart→compose |
| `release/sbom/aura-python.sbom.json` | CycloneDX 1.6 | cyclonedx-py 7.3.1 | 80 components, schema-valid |
| `release/sbom/aura-web.sbom.json` | CycloneDX 1.6 | cyclonedx-npm 6.0.1 | 350 components |

## Checksums

Checksums are generated at release packaging time from the wheel files; they
are not committed to source (they depend on build timestamps). To regenerate:

```bash
python -m build --wheel --outdir dist 06_SOURCE_CODE/aura
python -m build --wheel --outdir dist 06_SOURCE_CODE/aura-sdk
sha256sum dist/*.whl
```

## Status

- Python wheels: BUILT + INSTALLED + SMOKE-TESTED (clean install, Phase 17).
- Web build: BUILT + TESTED + AUDIT-CLEAN (Phase 21).
- Container image: BUILT + DEPLOYED + CYCLE-TESTED (Phase 18).
- SBOMs: GENERATED + VALIDATED (Phase 23).
- Version compatibility: `aura-sdk>=1.0.0` requires `aura>=0.2.0` (declared in
  its pyproject `dependencies` array); verified in the fresh-install test.