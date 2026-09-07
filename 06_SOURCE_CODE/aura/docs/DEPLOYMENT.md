# AURA Deployment Architecture (Phase 11)

## Environments

| Env        | Config file                 | Storage   | Enforced gates                                  |
| ---------- | --------------------------- | --------- | ----------------------------------------------- |
| LOCAL/DEV  | `config/env/development.yaml` | memory    | none (safe dev defaults)                         |
| TESTING    | `config/env/development.yaml` | memory    | tests always inject stores explicitly            |
| STAGING    | `config/env/staging.yaml`    | sqlite    | persistent backend required                      |
| PRODUCTION | `config/env/production.yaml`  | postgresql (interface) / sqlite | persistent backend + issuer secret >= 16 chars |

Production configuration is validated by
`scripts/validate_deployment.py` and enforced by `aura.api.server.run_server`
— the server **refuses to start** with an in-memory backend or a missing/weak
`AURA_API_SECRET`, and never silently downgrades a secure production config.

## Health/readiness/liveness

- `/liveness` — process alive; no dependency touch (used by container healthcheck).
- `/health` — engine status **plus** a real dependency round-trip
  (`store.count()` against the configured backend). Returns 503 when the
  dependency is down instead of a false "healthy".
- `/ready` — health + dependency; returns 200 only when work can be accepted.
- Security headers are set on every response regardless of the TLS terminator:
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `X-Request-Id`.

## Network / TLS

- The stdlib HTTP server is HTTP-only; **TLS termination is the reverse proxy's
  job** (Caddy/nginx/HAProxy in front). The proxy:
  - terminates HTTPS and forwards to `127.0.0.1:8765`;
  - sets `X-Forwarded-For` — consumed by the API **only** when the server is
    configured with `trust_proxy=true` (so a direct connection cannot spoof its
    rate-limit bucket);
  - is the boundary for WAF/rate shaping.
- Outbound connections are only made by the server to the configured storage
  backend; no third-party egress paths exist in the current runtime.

## Containerization

- `Dockerfile` — Python 3.12-slim, non-root `aura` user, `/data` volume writable
  by that user, `HEALTHCHECK` on `/liveness`.
- `compose.yaml` — dev stack with SQLite volume, healthcheck, restart policy.

## Secrets

- Secrets come from the environment (`AURA_PROVIDER_API_KEY`, `AURA_API_SECRET`,
  `AURA_ADMIN_KEY`); repository files (`config/env/*.yaml`, `.env.example`) only
  carry placeholders. The repo secret-scan is clean.