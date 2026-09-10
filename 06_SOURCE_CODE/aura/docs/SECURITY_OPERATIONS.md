# AURA Security Operations

## Secret handling

- No hardcoded production secrets in source; `.env` files are gitignored and
  absent from the tree.
- `.env.example` contains placeholders only.
- API keys are stored as **HMAC digests** (`aura.api.security.ApiKeyIssuer`,
  `aura.api.distributed.PostgreSQLApiKeyStore`); the raw key appears once at
  issuance in the API response.
- Logs and error responses redact secrets via `SecretRedactor`
  (`aura.observability.redaction`); audit entries carry IDs/decisions, never
  secret values.
- A repository secret scan runs in the release gate
  (`verify_ecosystem.py` → git grep for API-key assignments / private keys)
  and is clean.

## Authentication & authorization

- API: static bearer key and/or issued HMAC keys; admin-gated endpoints
  (`POST /v1/keys`, `POST /v1/keys/revoke`) require the admin key.
- Distributed deployments share keys/sessions/rate limits via PostgreSQL.
- Default deny: missing/invalid bearer → 401; insufficient privileges → 403.

## Dependency security

- `pip-audit 2.10.1` scans the runtime environment:
  **0 known vulnerabilities** (2026-09-10) after upgrading pip to 26.2.1.
  Evidence: `release/security/pip-audit.json`.
- `npm audit` on `aura-web`: **0 vulnerabilities** after `npm audit fix`
  (resolved 6 high + 2 moderate in dev/build transitive deps).
  Evidence: `release/security/npm-audit.json`.

## Includes of the security perimeter (verified)

- Request size limit (413 before reading body).
- Rate limiting (shared across instances; audit on deny).
- TLS termination at the reverse proxy (ephemeral test CA; header hardening).
- Proxy only trusts `X-Forwarded-For` when `trust_proxy=true`; the proxy
  overwrites XFF so clients cannot spoof identity.
- Fail-closed distributed-state outage behavior (deny on store unreachable).
- Prompt-injection boundary (`aura.security.prompt_injection.ContentPolicy`).

## Residual risks (documented, not hidden)

- TLS certs are operator-supplied; no public-cert automation exists.
- Multi-node rate limiting is PG-backed (single region) — cross-region
  distributed limits are not implemented.
- Audit falls back to a bounded in-process buffer during a store outage
  (records are not replayed to the durable store automatically).
- No alert delivery platform is wired (rules documented in
  `docs/OBSERVABILITY.md`).

## Security verification artifacts

- `release/security/pip-audit.json` — Python dependency scan (0 findings).
- `release/security/npm-audit.json` — web dependency scan (0 findings).
- Release-gate secret scan (no matches, clean).
- API security tests (`tests/security/`), TLS proxy tests
  (`tests/api/test_tls_proxy.py`), distributed-state outage tests.