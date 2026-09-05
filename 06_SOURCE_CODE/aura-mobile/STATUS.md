# STATUS: aura-mobile

## Architectural role
PARTIAL/AUTHORITATIVE mobile client ARCHITECTURE (coherent, tested). Clearly
distinguishes REAL IMPLEMENTATION / INTERFACE / SIMULATION. NO native Android
or iOS functionality is claimed (no buildable native code exists in this repo).

## Canonical owner
aura-mobile (standalone client; canonical runtime `aura/`).

## Implementation level
- Real authored files: 9 (app core, auth flow, network resilience, secure
  token store, offline queue, sync client, permission broker, sync queue)
- Scaffold/generated files: 0 (stubs removed/superseded)
- Broken: 0

## What is implemented
### REAL IMPLEMENTATION (in-memory, deterministic)
- `PermissionBroker` — default-deny capability checks.
- `SyncQueue` — ordered drain queue.
- `OfflineQueue` — ordered, bounded queue with retry attempts (never silently
  drops; `OverflowError` when full).
- `SyncClient` — offline-first: queues offline requests, flushes when online.

### INTERFACE / SIMULATION (clearly labeled)
- `AuthFlowContract` + `InMemoryAuthFlow` — login/logout/session contract;
  never stores plaintext secrets, uses the secure store for derived tokens.
- `SecureCredentialStore` INTERFACE + `InMemorySecureCredentialStore`
  (memory double; production keychain/keystore integration NOT claimed).
- `NetworkResilience` INTERFACE + `InMemoryNetwork` (deterministic with
  explicit online/offline control; no real network I/O).

## Explicit non-claims
- NO native Android implementation.
- NO native iOS implementation.
- NO OS keychain/keystore integration.
- NO real HTTP transport.

## Tests
- 13 passing. Covers: auth login/session/logout, empty-credential rejection,
  secure token storage (no plaintext claims, empty-token rejection), network
  offline failure and online request, offline queue bound + flush retry,
  sync client offline-queue/online-flush, mobile-core permission default-deny,
  privacy (no implicit telemetry), sync queue drain.

## Validation gates
- Syntax compilation: PASS
- Import validation: PASS
- Unit tests: PASS (13 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): NOT RUN (flat-layout; not configured in this session)
- Build/package check: NOT RUN (no native mobile build claimed)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone)
- PRODUCTION READY: INTERFACE/ARCHITECTURE (clearly labeled; no production
  mobile app claimed)
