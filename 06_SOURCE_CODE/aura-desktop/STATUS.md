# STATUS: aura-desktop

## Architectural role
PARTIAL/AUTHORITATIVE desktop client architecture (coherent, tested). This is
architecture + tests, NOT a claim of a packaged, buildable native desktop app.

## Canonical owner
aura-desktop (standalone client; canonical runtime `aura/`).

## Implementation level
- Real authored files: 8 (app entry, lifecycle, capability gate, storage,
  api client, diagnostics, settings)
- Scaffold/generated files: 0 (stub files removed/superseded)
- Broken: 0

## What is implemented (real behavior)
- `ApplicationLifecycle` — deterministic state machine
  (stopped->starting->running->stopping->stopped->failed) with invalid
  transition rejection and phase hooks.
- `CapabilityGate` — default-deny capability checks (`require` raises
  PermissionError when not granted).
- `SecureLocalStorage` INTERFACE + `InMemorySecureStorage` (explicitly an
  in-memory/test double; production keychain integration NOT claimed).
- `ApiClient` INTERFACE + `InMemoryApiClient` (deterministic, no network I/O).
- `SettingsStore` over secure local storage.
- `DiagnosticsRunner` with safe exception handling.
- `AuraDesktop` app facade composing lifecycle + capability gate.

## Explicit non-claims
- Does NOT claim a production desktop application that can be built/run as a
  native app.
- No OS keychain/credential vault integration.
- No real HTTP API transport beyond the interface contract.

## Tests
- 14 passing. Covers: lifecycle transitions/hooks/restart/invalid-transition,
  capability default-deny + require, secure storage roundtrip/delete,
  API client contract + memory client, settings persistence, diagnostics
  pass-fail + exception safety, AuraDesktop entry default-deny.

## Validation gates
- Syntax compilation: PASS
- Import validation: PASS
- Unit tests: PASS (14 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): NOT RUN (flat-layout; not configured in this session)
- Build/package check: NOT RUN (no native app packaging claimed)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone)
- PRODUCTION READY: INTERFACE/ARCHITECTURE (clearly labeled; not a production
  desktop application)
