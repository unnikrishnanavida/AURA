# PRODUCTION READINESS

This report intentionally uses the strict labels IMPLEMENTED / INTERFACE READY / PENDING.
Nothing is labelled production-ready without evidence.

## Gate evidence (what actually ran)

| Gate | Scope | Result |
|---|---|---|
| pytest | aura-agents/tests | 92 passed (0 failures) |
| pytest | aura/tests | passed (foundation..api, brain, sdk) |
| ruff | aura/src + tests | All checks passed |
| mypy (strict) | aura/src | Success: no issues |
| import validation | aura/src | all modules import cleanly |
| security scan | aura/src | no findings (shell/pickle/eval/secret) |
| package build | aura | wheel + sdist build; wheel import + Aura().health() ok |
| adaptive-defense tests | aura-security | passed (sandbox/approval/canary/rollback safety properties) |
| execution dry-run | aura-execution-complete | runs |
| CLI | aura | aura health / run / version verified |
| API | aura | /health /ready /reason /replay /openapi responded |

## IMPLEMENTED (canonical aura/) — operationally complete
foundation, config, core, memory, knowledge, reasoning, planning, execution, reflection, learning,
brain, security (incl. adaptive defense), observability (flight recorder/replay/provenance), providers,
research, sdk, api, cli.

## INTERFACE READY — adapters exist, external/optional
agents bridge (aura-agents guarded runtime, optional extra), provider adapters for external providers.

## PENDING — explicitly not claimed
- On-disk persistence adapters (SQLite/Postgres/Redis) - in-memory interfaces only
- Kubernetes manifests (compose/Docker real; K8s untested here)
- External provider SDK bindings
- Networking/streaming endpoints beyond the basic HTTP service

## Deployment
Dockerfile (non-root, healthcheck), compose.yaml (single service), CI workflow, .env.example present
for the canonical `aura/` repo. Standalone trees do not individually ship production containers.

## Keep-out / stance
There is a real security-scan and a real test suite backing the IMPLEMENTED claims above. AURA is not
claimed to be unhackable; security scanning is part of CI and improves continuously.
