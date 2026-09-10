# AURA SBOM (Software Bill of Materials)

Real CycloneDX 1.6 artifacts generated with established tooling — never
hand-fabricated.

## Artifacts

| File | Scope | Tool | Version | Date |
| ---- | ----- | ---- | ------- | ---- |
| `aura-python.sbom.json` | Python runtime environments (aura + aura-sdk + deps) | `cyclonedx-py` (CycloneDX Python) | 7.3.1 | 2026-09-10 |
| `aura-web.sbom.json` | Web frontend dependencies (prod + dev) | `@cyclonedx/cyclonedx-npm` | 6.0.1 | 2026-09-10 |

## Regeneration

Python:

```bash
cd <repo root>
.venv/Scripts/cyclonedx-py.exe environment \
  --pyproject 06_SOURCE_CODE/aura/pyproject.toml \
  --pyproject 06_SOURCE_CODE/aura-sdk/pyproject.toml \
  --output-reproducible --of json \
  -o 06_SOURCE_CODE/release/sbom/aura-python.sbom.json \
  .venv/Scripts/python.exe
```

Web:

```bash
cd 06_SOURCE_CODE/aura-web
npx --yes @cyclonedx/cyclonedx-npm \
  --output-file ../release/sbom/aura-web.sbom.json --output-format JSON
```

## Notes

- The Python SBOM reflects the live virtual environment resolved from the two
  pyproject manifests; `--output-reproducible` normalizes timestamps/serial
  numbers.
- The web SBOM includes the full installed tree (prod + dev) resolved from
  `package-lock.json`.
- Container image components are not separately listed because the image is
  not published; the base image (`python:3.12-slim`) digest is recorded in the
  Docker build output and the release manifest.