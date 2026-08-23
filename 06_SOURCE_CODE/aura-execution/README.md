# AURA Execution

A domain-specific execution subsystem for AURA. This repository implements the execution
vertical slice from planning input to validated result, with explicit capability,
permission, safety, budget, observation, recovery, state, provenance, replay, and telemetry
boundaries.

The implementation intentionally avoids universal `validate/execute/health` component
templates. Each domain owns its actual state transitions and decision rules.

## Pipeline

PlanningAdapter -> ExecutionRequest -> ActionResolver -> CapabilityRegistry
-> PermissionEngine -> SafetyEngine -> BudgetEngine -> Dispatcher
-> ToolAdapter -> ResultValidator -> Observation -> ExecutionResult
-> FlightRecorder -> Recovery on failure.

## Safety

Python and shell adapters are controlled interfaces. They require explicit allowlisting and
are disabled by default unless a caller supplies an approved executor. The HTTP/filesystem/
database adapters provide structured contracts and do not silently perform destructive work.

## Quick start

```bash
python -m pytest
python -m compileall aura_execution
python scripts/validate_architecture.py
```
