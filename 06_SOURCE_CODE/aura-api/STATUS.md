# STATUS: aura-api

## Architectural role
REUSABLE API LAYER (framework-agnostic contracts, security middleware,
validation, rate limiting, health/readiness, audit, versioning) + a socket-free
REFERENCE request processor. The production HTTP server is owned by the
canonical runtime (`aura.api.server`); aura-api does NOT compete with it.

## Canonical owner
`aura/src/aura/api` (canonical runtime `aura/`). aura-api provides reusable
API machinery and a reference adapter; the canonical runtime owns the actual
deployed HTTP service.

## Implementation level
- Real authored files (src): 22
- Scaffold/generated files: 0 (all 100% stub files removed)
- Broken: 0

## What is implemented (real behavior)
- Structured error taxonomy (`ApiError` hierarchy) with machine-readable codes
  and RFC-7807-style `ProblemDetails`; secrets are redacted from every error.
- Request validation (`RequestValidator`, `FieldSpec`) producing structured 400
  responses for missing/invalid/unknown fields.
- `RequestContext` with correlation IDs (generated or propagated from headers),
  request IDs, tenant, and principal binding.
- Fail-closed authentication (`Authenticator`, `ApiKeyStore`, HMAC secret
  hashing): malformed/missing/invalid/disabled credentials always -> 401.
- Fail-closed authorization (`RBACPolicy` + `ABACPolicy` + `Authorizer`):
  anonymous or unproven access -> 403.
- Rate limiting (`TokenBucket`, `SlidingWindow`, `CompositeLimiter`) -> 429.
- Health (`/health` liveness) and readiness (`/ready` dependency checks -> 503
  when a dependency is down).
- Audit logging of every denial with correlation ID.
- API versioning (`VersionRegistry`): path/header based, rejects unknown
  versions.
- Reference request processor (`ReferenceApi`) that demonstrates the full
  security pipeline without sockets — the canonical runtime wires a real
  server; this processor is what any framework adapter reuses.
- Security headers on every response (nosniff, frameguard, CSP, no-store).

## Tests
- 35 passing. Covers: invalid request, malformed payload, authentication
  failure, authorization failure, correlation ID propagation, secret/error
  redaction, health/readiness behavior, rate limiting, versioning, audit,
  full lifecycle e2e, canonical integration.

## Validation gates
- Syntax compilation: PASS (ast parse over all 22 src files)
- Import validation: PASS (`from aura_api import *` -> 45 exports)
- Unit + integration tests: PASS (35 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): PASS (exit 0)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (reusable layer + reference processor tested;
  package install/build not yet exercised)

## Known limitations
- Reference processor is socket-free; the canonical runtime owns the HTTP
  server deployment.
- In-memory rate limiting and audit are single-process.
- Authentication supports API-key credentials; OAuth/JWT is not implemented.
