# STATUS: aura-execution-complete

## Architectural role
HISTORICAL / SUPERSEDED prototype of the AURA execution runtime.

## Canonical owner
`aura-execution` (standalone) / `aura/src/aura/execution` (canonical runtime).

## Relationship to aura-execution
Both packages share the same top-level module name `aura_execution`, so they
cannot coexist in one interpreter. `aura-execution-complete` is preserved here
as a HISTORICAL reference and its legacy tests still pass, but the
AUTHORITATIVE execution runtime is `aura-execution`. No in-process bridge is
possible.

## Implementation level
- Real authored files: ~80 (all originally-authored minimal engine)
- Scaffold/generated files: 0
- Broken: 0

## Tests
- 2 passing (`test_execution.py`, `test_budget.py`) — simple happy-path
  legacy coverage.

## Validation gates
- Unit tests: PASS (2 passed)
- Lint / type check: NOT RUN (historical reference repo)

## Supported runtime status
- IMPORTED BY RUNTIME: No (HISTORICAL/SUPERSEDED)
- PRODUCTION READY: NOT SUPPORTED for new code (preserved for reference)