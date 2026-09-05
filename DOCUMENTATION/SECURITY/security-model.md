# AURA Security Model

## Verified security primitives (canonical aura/security)

- **Capabilities** — explicit `namespace.verb` matching; unknown capability is
  denied (default deny).
- **Permissions** — resolution `Identity -> Scope -> Policy -> Risk -> Approval`
  producing ALLOW / DENY / APPROVAL_REQUIRED.
- **Safety** — explicit ALLOW / REVIEW / DENY decisions with explanation.
- **Autonomy** — autonomy levels never bypass permission/safety/budget.
- **Budgets** — multi-dimensional (actions, cost, tokens, api-calls, time).
- **Recovery** — single authoritative recovery classifier and strategy set
  (RETRY / FALLBACK / COMPENSATE / ROLLBACK / REPLAN / ESCALATE / ABORT).
- **Audit** — append-only audit log of security-relevant decisions.
- **Redaction** — secrets/keys/tokens never logged.
- **Learning gate** — safety-relevant learned updates require explicit
  authorization and are versioned/rollback-able.

## Adaptive defense (aura-security standalone engine)

The remediation lifecycle is strictly bounded and never self-deploys to
production:

```
DETECT -> CLASSIFY -> ANALYZE -> CONTROL-GAP -> SELECT DEFENSE
  -> REMEDIATION SPEC -> TEST SPEC -> SANDBOX -> STATIC VALIDATION
  -> SECURITY VALIDATION -> REGRESSION -> APPROVAL GATE -> CANARY
  -> MONITOR -> ROLLBACK IF NECESSARY
```

Tests verify: low-severity threats never propose; missing/same-as-requester
approver blocks; high-severity requires a security role; unhealthy canary never
activates; activation only via injected callbacks; every transition audited.

## Fail-closed rules

- Security middleware must fail closed (no silent fail-open).
- Invalid requests produce structured errors without exposing internals.
- No capability bypasses permission -> safety -> budget.