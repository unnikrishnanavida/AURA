# AURA API Reference

The canonical runtime exposes:

- `from aura import Aura` (SDK) — `aura.reason(...)`, `aura.plan(...)`,
  `aura.execute(...)`, `aura.remember(...)`, `aura.recall(...)`,
  `aura.replay(...)`, `aura.health()`.
- HTTP service under `06_SOURCE_CODE/aura/src/aura/api` — endpoints include
  health, readiness, reasoning, replay, and OpenAPI. Routes are thin; domain
  logic lives in services. Correlation/execution IDs ride on every request.

## Error model

Structured errors; sensitive information is never included. Security failures
fail closed.

## Auth / authorization

Authentication and authorization integration hooks exist in the canonical API
and in the standalone `aura-api` compatibility layer. The standalone `aura-api`
auth modules (api-key, token, principal, RBAC/ABAC policy engines) are real;
most of its other modules are scaffold.

## Validation evidence

- Canonical API tests pass.
- Live smoke: `/health`, `/ready`, `/v1/reason`, `/v1/replay/{id}`,
  `/openapi.json` responded 200 with correlation IDs (previous verified pass).