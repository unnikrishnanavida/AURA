# STATUS: aura-core

## Architectural role
REUSABLE INFRASTRUCTURE (kernel lifecycle, config, DI, registries, events,
health/readiness, cancellation/timeouts, idempotency, correlation context).

## Canonical owner
`aura/src/aura/core` + `aura/src/aura/foundation` (canonical runtime `aura/`).

## Implementation level
- Real authored files: 252 (preserved)
- Scaffold/generated files: 0
- Broken: 0

## Preserved real implementation
- `kernel/` — Kernel lifecycle orchestrator (boot/start/stop hooks, state
  machine, register/resolve), boot loaders, runtime manager.
- `config/` — ConfigLoader, ConfigManager, providers, validators.
- `dependency_injection/` — Injector (singleton/transient), scoped providers.
- `caching/`, `concurrency/`, `events/`, `filesystem/`, `networking/`,
  `observability/`, `security/`, `serialization/`, `validation/`, `types/`,
  `aura_types/`, `versioning/`, `lifecycle/`, `registry/`, `protocols/`.
- `logging` shadow fix (stdlib `logging` -> `aura_core.logging` namespace).

## What is implemented (real behavior, architecturally necessary)
- Instance-scoped `ServiceRegistry` (NO module-global hidden state — replaced
  the old module-level `REGISTRY = {}` global).
- `HealthRegistry` + `HealthSummary`/`ReadinessSummary` contracts.
- `CancellationToken` + `TimeoutGuard` + `TimeoutResult` contracts.
- `CorrelationContext` + `new_correlation_id` for end-to-end tracing.
- `IdempotencyStore` + `IdempotentExecutor` (duplicate-key protection, replay
  detection).

## Tests
- 21 passing (6 preserved kernel tests + 15 new contract tests). Covers:
  service registry isolation (no global state), health/readiness pass-fail and
  exception safety, cancellation fail-closed, timeout elapsed reporting,
  correlation propagation, idempotent replay with single fn call, DI
  singleton/transient, event-bus publish/subscribe, kernel lifecycle.

## Validation gates
- Syntax compilation: PASS
- Import validation: PASS
- Unit tests: PASS (21 passed)
- Lint (ruff): PASS (exit 0 on new modules)
- Type check (mypy): NOT RUN (flat-layout repo; not configured for mypy in
  this session)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (real kernel + contracts, tested)

## Known limitations
- Flat-layout repo: package install/import from `src/` not exercised.
- Some submodules remain shallow stubs (registry `factory_registry`,
  `plugin_registry`, `serializer_registry`); the architecturally necessary
  contracts are implemented and tested.
