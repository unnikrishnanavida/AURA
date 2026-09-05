# AURA Security

Summary of the AURA security posture; the full model lives in
`06_SOURCE_CODE/aura/SECURITY.md` and `06_SOURCE_CODE/aura/docs/architecture.md`.

- **Capability-based execution** — nothing runs without an explicit grant.
- **Permission decisions** — ALLOW / DENY / APPROVAL_REQUIRED, default deny.
- **Safety decisions** — ALLOW / REVIEW / DENY, always explainable.
- **Autonomy never bypasses safety** — increasing autonomy only raises the
  auto-approval ceiling.
- **Budgets** bound actions, time, cost, and tokens.
- **Learning is gated** — safety-relevant changes require explicit
  authorization.
- **Secrets** are loaded from the environment, never committed, and always
  redacted in logs and dumps.

Run the audit with:

```bash
cd 06_SOURCE_CODE/aura && python scripts/security_check.py
```

## Vulnerability reporting

Report suspected security defects privately to the maintainers, including the
affected version, a minimal reproduction, and observed impact. Public issues
should not be used for confirmed or suspected security defects.
