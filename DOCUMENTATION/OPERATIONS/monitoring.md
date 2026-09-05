# AURA Monitoring & Operations

## Observability (canonical aura/observability)

- Structured, redacting logs with correlation/execution IDs.
- Metrics (execution count, success/failure rate, latency, retries, budgets,
  tool/provider failures).
- Intelligence Flight Recorder: event streams per execution with IDs,
  timestamps, source, type, sequence, payload.
- Replay: reconstruct trajectories; explicit RECORDED vs RECONSTRUCTED state.
- Provenance graph: `Goal -> Reasoning -> Decision -> Plan -> Action -> Tool ->
  Observation -> Evaluation -> Reflection -> Learning`.

## Health & readiness

- Health endpoint reports component liveness; readiness reports dependency
  readiness.
- CLI exposes `aura health`, `aura ready`-equivalent behavior in the canonical
  CLI.

## Incident response

- `aura-security` adaptive-defense pipeline ends in a rollback-capable canary
  flow; see `DOCUMENTATION/SECURITY/security-model.md`.

## Backup / recovery

- Memory is injected and can be persisted behind interfaces; execution
  checkpoints and compensation actions are defined. No on-disk adapter ships
  yet (documented limitation).