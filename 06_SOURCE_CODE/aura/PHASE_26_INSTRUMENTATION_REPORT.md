# Phase 26 — Metrics Instrumentation Report

**Status:** COMPLETE for 5 of 6 metrics; **provider_failure documented as NOT INSTRUMENTED** (architectural blocker, explained below).

---

## 1. Previous state

Phase 26 delivered the alerting infrastructure:

- `AlertManager.evaluate()` works, `AlertManager.health()` works.
- `ServiceDown` alert fires on unhealthy dependency.
- Webhook delivery works and `delivered_count` increments.
- `/health` exposes `alerts_fired` + `alert_health`; the evaluation path is exception-safe.

**Gap:** the default alert rules referenced six counter metrics that had **no production call sites**:

| Metric | Default rule | Production `increment()` sites before |
|--------|--------------|----------------------------------------|
| `api_auth_failure` | AuthenticationAttack | 0 |
| `rate_limit_deny` | ExcessiveRateLimit | 0 |
| `memory_operation_failure` | PersistenceFailure | 0 |
| `provider_failure` | ProviderFailure | 0 |
| `execution_count` | HighErrorRate (numerator) | 0 |
| `execution_failure` | HighErrorRate (ratio) | 0 |

The rules read `snapshot["counters"][...]`, so counters that were never
incremented stayed at zero and the alert rules could never fire.

## 2. Root cause

The metrics registry (`aura/observability/metrics.py`) was fully wired into
`Brain.metrics` and exported via `Aura.metrics()`, but no runtime layer ever
called `Metrics.increment(...)` for the six documented counters. The event
boundaries existed in the code (401, 429, store failures, reasoning
executions) but were not connected to the registry.

## 3. Files changed

| File | Change |
|------|--------|
| `src/aura/memory/engine.py` | Added `metrics` injection + `_count_store_failure` decorator over store-backed operations; per-thread re-entrancy depth guards single-increment semantics; type-preserving decorator (`F = TypeVar`) |
| `src/aura/brain/engine.py` | `BrainEngine.create()` builds `Metrics` once and wires it into `MemoryEngine`; `BrainEngine.reason()` split into public instrumented `reason()` + `_reason_impl()` |
| `src/aura/api/server.py` | `_require_auth()` increments `api_auth_failure` on a genuine 401; `_check_rate_limit()` increments `rate_limit_deny` on a genuine 429 |
| `tests/observability/test_phase26_instrumentation.py` | NEW — metric-level tests (auth, rate limit, memory, execution, concurrency) |
| `tests/observability/test_phase26_alert_integration.py` | NEW — end-to-end alert tests incl. webhook delivery and `/health` preservation |

## 4. Metrics added (production semantics)

| Metric | Meaning | Unit | Increment point | Cumulative | Reset | Process-local | Alert rule |
|--------|---------|------|-----------------|-----------|-------|---------------|------------|
| `api_auth_failure` | API authentication denials | count (1 per 401) | `Handler._require_auth()` when `_authorized()` is False | yes | none (process lifetime) | yes (`RLock` defaultdict registry, in-process) | AuthenticationAttack (counter > 50) |
| `rate_limit_deny` | API rate-limit denials | count (1 per 429) | `Handler._check_rate_limit()` when `RateLimiter.allow()` is False | yes | none | yes | ExcessiveRateLimit (counter > 100) |
| `memory_operation_failure` | genuine store-backed memory operation failures | count (1 per non-`NotFound`/non-`ValueError` store exception) | every store-touching `MemoryEngine` operation via `_count_store_failure` | yes | none | yes | PersistenceFailure (counter > 10) |
| `provider_failure` | provider invocation failures | count | **NOT INSTRUMENTED** (blocker in §11) | n/a | n/a | n/a | ProviderFailure (rule intact but dormant) |
| `execution_count` | cognitive execution attempts | count (1 per `BrainEngine.reason()`) | `BrainEngine.reason()` entry | yes | none | yes | HighErrorRate numerator |
| `execution_failure` | execution attempts that raised | count (1 per failed `BrainEngine.reason()`) | `BrainEngine.reason()` except branch | yes | none | yes | HighErrorRate ratio |

- **Successful behavior:** success never touches the matching failure
  counters (`api_auth_failure`, `rate_limit_deny`, `memory_operation_failure`,
  `execution_failure` stay flat).
- **Failure behavior:** one real event → **one** increment on its metric.
- **Consumer:** `AlertManager.evaluate(snapshot, health)` reads
  `counters[name]` via `AlertRule._read`; the error-rate rule computes
  `execution_failure / execution_count`.

## 5. Exact production call sites

Source-level audit (`metrics.increment(` in `src/`, tests excluded):

| Metric | Call site |
|--------|-----------|
| `api_auth_failure` | `src/aura/api/server.py:440` — `_require_auth()` when auth denied |
| `rate_limit_deny` | `src/aura/api/server.py:418` — `_check_rate_limit()` when limiter denies |
| `memory_operation_failure` | `src/aura/memory/engine.py:90` — `_count_store_failure` decorator |
| `provider_failure` | (none — NOT INSTRUMENTED) |
| `execution_count` | `src/aura/brain/engine.py:156` — `reason()` entry |
| `execution_failure` | `src/aura/brain/engine.py:170` — `reason()` except branch |

Each metric has **exactly one** production call site.

## 6. Alert rules affected

- `AuthenticationAttack` — now driven by real 401 denials.
- `ExcessiveRateLimit` — now driven by real 429 denials.
- `PersistenceFailure` — now driven by real store failures.
- `ProviderFailure` — rule unchanged; metric has no production call site (§11).
- `HighErrorRate` — now derived from real `execution_count` + `execution_failure`.
- `ServiceDown`, `HighLatency` — unchanged (health- and latency-driven).

## 7. Double-counting analysis

| Trace | Result |
|-------|--------|
| 1 failed auth | `api_auth_failure` **+1** (single site in `_require_auth`; `_check_rate_limit` is never reached on a 401, so no cross-count) |
| 1 rate-limit denial | `rate_limit_deny` **+1** (single site in `_check_rate_limit`, called once per request) |
| 1 memory store exception | `memory_operation_failure` **+1** — nested ops (`archive` → `by_id`) guarded by a per-thread re-entrancy depth so the outermost boundary counts exactly once |
| 1 failed execution | `execution_count` **+1**, `execution_failure` **+1** (one boundary, one increment each) |
| 1 successful execution | `execution_count` **+1**, `execution_failure` **+0** |
| memory failure during an execution | `memory_operation_failure` +1 AND `execution_failure` +1 — two different metrics for two real events (the store failed; the execution failed because of it). Neither metric is incremented twice. |

Tests `test_failed_auth_does_not_increment_rate_limit_metric`,
`test_rate_limit_denial_increments_exactly_once_per_429`,
`test_nested_memory_operation_counts_once_per_event`, and
`test_execution_*` lock this in.

## 8. Tests added

`tests/observability/test_phase26_instrumentation.py`:

- `test_failed_auth_increments_api_auth_failure_exactly_once`
- `test_successful_auth_does_not_increment_api_auth_failure`
- `test_failed_auth_does_not_increment_rate_limit_metric`
- `test_rate_limit_denial_increments_exactly_once_per_429`
- `test_rate_limit_success_does_not_increment`
- `test_memory_operation_failure_increments_exactly_once`
- `test_memory_not_found_is_not_a_failure`
- `test_memory_validation_error_is_not_a_failure`
- `test_successful_memory_operation_not_counted_as_failure`
- `test_nested_memory_operation_counts_once_per_event`
- `test_execution_success_increments_count_only`
- `test_execution_failure_increments_count_and_failure`
- `test_metrics_increment_is_thread_safe`

`tests/observability/test_phase26_alert_integration.py`:

- `test_auth_attack_fires_alert_and_delivers_webhook` (real 401s → metric → alert → webhook payload → delivered_count)
- `test_excessive_rate_limit_fires_alert_from_real_denials`
- `test_persistence_failure_fires_alert_from_real_memory_failures`
- `test_high_error_rate_fires_from_real_executions`
- `test_provider_failure_rule_consumes_provider_failure_counter`
- `test_health_endpoint_preserves_alerts_fields_and_semantics`

## 9. Test results

- `pytest tests/observability tests/api tests/security` → **passes**
- Full suite (`pytest tests`) → **exit 0** (all observability/api/security + Phase-26 tests green)
- `py_compile src/aura/memory/engine.py src/aura/brain/engine.py src/aura/api/server.py` → **exit 0**
- `ruff check` on all changed files → **All checks passed**
- `mypy src/aura/memory/engine.py src/aura/brain/engine.py src/aura/api/server.py` → **no issues**

## 10. Alert smoke-test results

The end-to-end `AuthenticationAttack` test confirms:

    51 real 401 events
        → api_auth_failure == 51
        → /health runs _evaluate_alerts
        → AuthenticationAttack fires
        → JSON payload delivered to the webhook sink
        → delivered_count >= 1

`ExcessiveRateLimit`, `PersistenceFailure`, and `HighErrorRate` each fire from
real events (429s, broken-store remembers, real reasoning executions).

## 11. Remaining limitations

### provider_failure — NOT INSTRUMENTED

**Architectural blocker (verified by source audit, not inferred):**

- The reasoning runtime path is:
  `Aura.reason() -> BrainEngine.reason() -> ReasoningEngine.reason()`
  which **never enters** the `aura.providers` abstraction.
- `aura/providers/embedded.py :: EmbeddedReasoningProvider.reason()` exists but
  has **zero production callers** (checked across `src/`, `tests/`,
  `aura-agents/`, `evaluation/`, `aura-web/`). The only `.provider.reason()`
  call site in the repository lives in the **separate** `aura-agents` package
  (`aura_agent/reasoning_bridge/reasoning_adapter.py`), which uses its own
  `ReasoningProvider` protocol and has no access to `aura`'s `Brain.metrics`.
- The `providers` package currently models profiles and selection only;
  external providers (OpenAI/Anthropic/Gemini/Groq/Ollama) are not wired into
  the runtime.

Per the Phase-26 failure rule (§15) this must **not** be faked with a
test-only call site. Instrumenting `EmbeddedReasoningProvider.reason()`
today would be dead code in production, so it is documented as **NOT
INSTRUMENTED**. The `ProviderFailure` alert rule is intentionally left intact:
it consumes `provider_failure` from the snapshot (verified by
`test_provider_failure_rule_consumes_provider_failure_counter`) and will fire
the moment a real provider boundary is wired.

### Other notes

- Metrics are process-local and cumulative for the process lifetime (same as
  the pre-existing `Metrics` design — no new subsystem introduced). They are
  reset only by process restart, and `/v1/metrics` reports the live snapshot.
- `api_auth_failure` counts API-key authentication failures specifically;
  the admin key gate (`/v1/keys`, 403) is authorization, not authentication,
  and is intentionally excluded.

## 12. Final Phase-26 status

| Acceptance criterion | Status |
|----------------------|--------|
| `api_auth_failure` has genuine call sites | **PASS** |
| `rate_limit_deny` has genuine call sites | **PASS** |
| `memory_operation_failure` has genuine call sites | **PASS** |
| `provider_failure` has genuine call sites | **NOT VERIFIED** (architectural blocker; documented in §11) |
| `execution_count` has genuine call sites | **PASS** |
| `execution_failure` has genuine call sites | **PASS** |
| no metric is double-counted | **PASS** (single-site audit + nested-op re-entrancy guard + tests) |
| successful operations are not counted as failures | **PASS** |
| alert rules consume live metrics | **PASS** |
| actual events can trigger alerts | **PASS** |
| webhook delivery remains functional | **PASS** |
| `/health` remains functional (alerts_fired + alert_health, 200/503) | **PASS** |
| no secret leakage | **PASS** (payload contract unchanged; redactor untouched) |
| concurrency behavior is safe | **PASS** (`RLock` + thread-safety test) |
| existing tests remain green | **PASS** |
| new regression tests pass | **PASS** |
| full suite passes | **PASS** |

**Phase 26 is COMPLETE except `provider_failure`**, which requires a genuine
provider invocation boundary to be introduced by a future phase (wiring
reasoning through the provider abstraction, or adding a real external-provider
adapter). Until then, no fake instrumentation was added.