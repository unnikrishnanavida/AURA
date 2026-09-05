# AURA Deployment

## Canonical `aura/` deployment assets

`06_SOURCE_CODE/aura/` ships:

- **Dockerfile** — non-root 3.12 image with HEALTHCHECK, `AURA_ENVIRONMENT=production`.
- **compose.yaml** — single `aura-api` service with healthcheck.
- **.github/workflows/ci.yml** — lint -> type -> imports -> pytest -> security -> build -> wheel smoke -> Docker.
- **.env.example** — documented environment variables.

Build the image:

```sh
cd 06_SOURCE_CODE/aura
docker build -t aura:latest .
```

Run via compose:

```sh
docker compose up -d
```

## Environment configuration

Environments: `development`, `testing`, `research`, `staging`, `production`.
Configuration is typed (`AuraConfig`) and validated at startup; secrets come
from environment/secret providers, never from source.

## NOT RUN (honest)

- Kubernetes manifests: **not validated** against a real cluster.
- Cloud provider deployment: **simulated only** (no credentials; `aura-cloud`
  uses a simulator + policy gates).

## Rollback

- Execution and adaptive-defense components expose rollback/compensation
  contracts; canary + monitor + rollback flow is tested in `aura-security`.