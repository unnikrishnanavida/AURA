# STATUS: aura-cli

## Architectural role
AUTHORITATIVE standalone CLI that calls REAL functionality in the canonical
runtime (`aura/`) and the standalone subsystem packages (aura-knowledge,
aura-reflection, aura-api) through explicit adapters. No command prints
"Success"/"Done" without performing real work.

## Canonical owner
`aura/src/aura/cli` (canonical runtime `aura/` owns an installed `aura`
command). aura-cli is the standalone developer/admin CLI exposing the same
contracts plus the standalone subsystem commands.

## Implementation level
- Real authored files (src): 15
- Scaffold/generated files: 0 (all 100% stub files removed)
- Broken: 0

## Implemented commands (real behavior)
- `aura doctor`            — real dependency/import diagnostics with per-check results.
- `aura health`            — canonical runtime health + per-subsystem availability.
- `aura config validate`   — loads a real JSON profile and validates it (exit 2 on invalid).
- `aura run <question>`    — real reasoning pass via the canonical `Aura` SDK.
- `aura knowledge`         — real aura-knowledge engine exercise (adds + verifies a claim).
- `aura plan <goal>`       — real canonical planning engine plan creation.
- `aura security audit`    — real canonical audit log tail; dangerous op requiring confirmation.
- `aura version`           — real package version.

## Cross-cutting behavior
- Stable exit codes (`ExitCode`: 0 ok, 1 failed, 2 config invalid/usage,
  3 not found, 4 denied, 5 not supported, 70 internal).
- Human-readable text and JSON output (`--output json`).
- Non-interactive mode fails closed for dangerous operations unless `--yes`.
- Configuration profiles (JSON) with `ProfileLoader` and validation.
- Structured `CommandResult` with machine-readable error codes.
- Explicit adapters; unreachable engines report `not_supported` honestly.

## Tests
- 18 passing. Covers: successful command, failure command, JSON output,
  invalid configuration, stable exit codes, non-interactive mode, dangerous
  operation confirmation behavior, real canonical calls, plan/knowledge/health.

## Validation gates
- Syntax compilation: PASS (ast parse over all 15 src files)
- Import validation: PASS (`python -m aura_cli version` runs)
- Unit tests: PASS (18 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): PASS (exit 0)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone CLI; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (real commands, stable exit codes, tested)

## Known limitations
- `research`, `replay`, `security status` (beyond audit) are not yet wired to
  a real backing engine in the standalone CLI.
- Networking/streaming not offered by this CLI.
