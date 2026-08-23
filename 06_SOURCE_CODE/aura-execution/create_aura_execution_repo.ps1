[CmdletBinding()]
param(
    [string]$Root = "C:\Users\navid\Desktop\AURA\06_SOURCE_CODE",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoName = "aura-execution"
$Repo = Join-Path $Root $RepoName

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "       AURA EXECUTION REPOSITORY SETUP" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# DIRECTORY STRUCTURE
# ------------------------------------------------------------

$Directories = @(
    "aura_execution"

    "aura_execution/kernel"
    "aura_execution/kernel/lifecycle"
    "aura_execution/kernel/runtime"
    "aura_execution/kernel/identity"

    "aura_execution/contracts"
    "aura_execution/contracts/requests"
    "aura_execution/contracts/responses"
    "aura_execution/contracts/protocols"
    "aura_execution/contracts/schemas"

    "aura_execution/orchestration"
    "aura_execution/orchestration/routing"
    "aura_execution/orchestration/pipelines"
    "aura_execution/orchestration/coordination"

    "aura_execution/actions"
    "aura_execution/actions/models"
    "aura_execution/actions/preparation"
    "aura_execution/actions/dispatch"

    "aura_execution/capabilities"
    "aura_execution/capabilities/models"
    "aura_execution/capabilities/registry"
    "aura_execution/capabilities/matching"

    "aura_execution/tools"
    "aura_execution/tools/models"
    "aura_execution/tools/registry"
    "aura_execution/tools/adapters"

    "aura_execution/permissions"
    "aura_execution/permissions/models"
    "aura_execution/permissions/policies"
    "aura_execution/permissions/approval"

    "aura_execution/safety"
    "aura_execution/safety/models"
    "aura_execution/safety/analysis"
    "aura_execution/safety/gates"

    "aura_execution/sandbox"
    "aura_execution/sandbox/environments"
    "aura_execution/sandbox/policies"
    "aura_execution/sandbox/lifecycle"

    "aura_execution/concurrency"
    "aura_execution/concurrency/scheduling"
    "aura_execution/concurrency/coordination"

    "aura_execution/transactions"
    "aura_execution/transactions/models"
    "aura_execution/transactions/lifecycle"
    "aura_execution/transactions/compensation"

    "aura_execution/checkpoints"
    "aura_execution/checkpoints/models"
    "aura_execution/checkpoints/storage"
    "aura_execution/checkpoints/recovery"

    "aura_execution/recovery"
    "aura_execution/recovery/models"
    "aura_execution/recovery/classification"
    "aura_execution/recovery/strategies"

    "aura_execution/validation"
    "aura_execution/validation/preconditions"
    "aura_execution/validation/results"
    "aura_execution/validation/consistency"

    "aura_execution/observation"
    "aura_execution/observation/models"
    "aura_execution/observation/collection"
    "aura_execution/observation/analysis"

    "aura_execution/execution_state"
    "aura_execution/execution_state/models"
    "aura_execution/execution_state/transitions"

    "aura_execution/budgets"
    "aura_execution/budgets/models"
    "aura_execution/budgets/tracking"

    "aura_execution/action_genome"
    "aura_execution/action_genome/identity"
    "aura_execution/action_genome/performance"
    "aura_execution/action_genome/lineage"

    "aura_execution/flight_recorder"
    "aura_execution/flight_recorder/events"
    "aura_execution/flight_recorder/storage"
    "aura_execution/flight_recorder/reconstruction"

    "aura_execution/replay"
    "aura_execution/replay/snapshots"
    "aura_execution/replay/runner"

    "aura_execution/provenance"
    "aura_execution/provenance/models"
    "aura_execution/provenance/graph"

    "aura_execution/reasoning_bridge"
    "aura_execution/reasoning_bridge/inputs"

    "aura_execution/planning_bridge"
    "aura_execution/planning_bridge/inputs"
    "aura_execution/planning_bridge/conversion"

    "aura_execution/memory_bridge"
    "aura_execution/memory_bridge/retrieval"
    "aura_execution/memory_bridge/writing"

    "aura_execution/learning_bridge"
    "aura_execution/learning_bridge/signals"
    "aura_execution/learning_bridge/strategy"

    "aura_execution/planning_feedback"
    "aura_execution/planning_feedback/models"

    "aura_execution/multi_agent"
    "aura_execution/multi_agent/coordination"
    "aura_execution/multi_agent/synchronization"

    "aura_execution/telemetry"
    "aura_execution/telemetry/metrics"
    "aura_execution/telemetry/logging"
    "aura_execution/telemetry/monitoring"

    "aura_execution/configuration"
    "aura_execution/configuration/defaults"
    "aura_execution/configuration/profiles"

    "aura_execution/api"
    "aura_execution/api/http"
    "aura_execution/api/schemas"

    "tests"
    "tests/unit"
    "tests/unit/actions"
    "tests/unit/capabilities"
    "tests/unit/tools"
    "tests/unit/permissions"
    "tests/unit/safety"
    "tests/unit/recovery"
    "tests/unit/validation"
    "tests/unit/observation"
    "tests/unit/transactions"
    "tests/unit/budgets"

    "tests/integration"
    "tests/integration/planning"
    "tests/integration/reasoning"
    "tests/integration/memory"
    "tests/integration/learning"
    "tests/integration/execution"

    "tests/security"
    "tests/recovery"
    "tests/replay"
    "tests/property"

    "benchmarks"
    "benchmarks/execution"
    "benchmarks/recovery"
    "benchmarks/concurrency"
    "benchmarks/end_to_end"

    "evaluation"
    "evaluation/evaluators"
    "evaluation/datasets"
    "evaluation/gates"

    "examples"
    "examples/basic_execution"
    "examples/recovery"
    "examples/sandbox"
    "examples/parallel"
    "examples/full_pipeline"

    "docs"
    "docs/architecture"
    "docs/execution"
    "docs/security"
    "docs/evaluation"

    "scripts"
)

# ------------------------------------------------------------
# FILE STRUCTURE
# ------------------------------------------------------------

$Files = @(
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "SECURITY.md"
    "CODE_OF_CONDUCT.md"
    "pyproject.toml"
    "Makefile"
    "Dockerfile"
    ".gitignore"

    # Kernel
    "aura_execution/kernel/kernel.py"
    "aura_execution/kernel/lifecycle/bootstrap.py"
    "aura_execution/kernel/lifecycle/shutdown.py"
    "aura_execution/kernel/lifecycle/health.py"
    "aura_execution/kernel/lifecycle/lifecycle_manager.py"
    "aura_execution/kernel/runtime/execution_runtime.py"
    "aura_execution/kernel/runtime/execution_context.py"
    "aura_execution/kernel/runtime/runtime_state.py"
    "aura_execution/kernel/runtime/resource_tracker.py"
    "aura_execution/kernel/identity/execution_id.py"
    "aura_execution/kernel/identity/execution_fingerprint.py"
    "aura_execution/kernel/identity/attempt_id.py"

    # Contracts
    "aura_execution/contracts/requests/execution_request.py"
    "aura_execution/contracts/requests/resume_request.py"
    "aura_execution/contracts/requests/cancel_request.py"
    "aura_execution/contracts/requests/approval_request.py"
    "aura_execution/contracts/responses/execution_result.py"
    "aura_execution/contracts/responses/action_result.py"
    "aura_execution/contracts/responses/execution_status.py"
    "aura_execution/contracts/responses/recovery_result.py"
    "aura_execution/contracts/protocols/executor_protocol.py"
    "aura_execution/contracts/protocols/tool_protocol.py"
    "aura_execution/contracts/protocols/recovery_protocol.py"
    "aura_execution/contracts/protocols/observer_protocol.py"
    "aura_execution/contracts/schemas/execution_schema.py"
    "aura_execution/contracts/schemas/action_schema.py"
    "aura_execution/contracts/schemas/result_schema.py"
    "aura_execution/contracts/schemas/error_schema.py"

    # Orchestration
    "aura_execution/orchestration/orchestrator.py"
    "aura_execution/orchestration/routing/executor_router.py"
    "aura_execution/orchestration/routing/capability_router.py"
    "aura_execution/orchestration/routing/tool_router.py"
    "aura_execution/orchestration/pipelines/execution_pipeline.py"
    "aura_execution/orchestration/pipelines/validation_pipeline.py"
    "aura_execution/orchestration/pipelines/recovery_pipeline.py"
    "aura_execution/orchestration/coordination/execution_coordinator.py"
    "aura_execution/orchestration/coordination/parallel_coordinator.py"
    "aura_execution/orchestration/coordination/dependency_coordinator.py"

    # Actions
    "aura_execution/actions/action_engine.py"
    "aura_execution/actions/models/executable_action.py"
    "aura_execution/actions/models/action_input.py"
    "aura_execution/actions/models/action_output.py"
    "aura_execution/actions/models/action_context.py"
    "aura_execution/actions/preparation/action_preparer.py"
    "aura_execution/actions/preparation/input_resolver.py"
    "aura_execution/actions/preparation/precondition_validator.py"
    "aura_execution/actions/dispatch/action_dispatcher.py"
    "aura_execution/actions/dispatch/dispatch_strategy.py"
    "aura_execution/actions/dispatch/dispatch_result.py"

    # Capabilities
    "aura_execution/capabilities/capability_engine.py"
    "aura_execution/capabilities/models/capability.py"
    "aura_execution/capabilities/models/capability_requirement.py"
    "aura_execution/capabilities/models/capability_metadata.py"
    "aura_execution/capabilities/registry/capability_registry.py"
    "aura_execution/capabilities/registry/capability_resolver.py"
    "aura_execution/capabilities/registry/capability_health.py"
    "aura_execution/capabilities/matching/capability_matcher.py"
    "aura_execution/capabilities/matching/compatibility.py"

    # Tools
    "aura_execution/tools/tool_engine.py"
    "aura_execution/tools/models/tool.py"
    "aura_execution/tools/models/tool_input.py"
    "aura_execution/tools/models/tool_output.py"
    "aura_execution/tools/models/tool_metadata.py"
    "aura_execution/tools/registry/tool_registry.py"
    "aura_execution/tools/registry/tool_resolver.py"
    "aura_execution/tools/registry/tool_health.py"
    "aura_execution/tools/adapters/python_adapter.py"
    "aura_execution/tools/adapters/shell_adapter.py"
    "aura_execution/tools/adapters/http_adapter.py"
    "aura_execution/tools/adapters/filesystem_adapter.py"
    "aura_execution/tools/adapters/database_adapter.py"

    # Permissions
    "aura_execution/permissions/permission_engine.py"
    "aura_execution/permissions/models/permission.py"
    "aura_execution/permissions/models/permission_scope.py"
    "aura_execution/permissions/models/authorization_context.py"
    "aura_execution/permissions/policies/permission_policy.py"
    "aura_execution/permissions/policies/capability_policy.py"
    "aura_execution/permissions/policies/resource_policy.py"
    "aura_execution/permissions/approval/approval_request.py"
    "aura_execution/permissions/approval/approval_manager.py"
    "aura_execution/permissions/approval/approval_gate.py"

    # Safety
    "aura_execution/safety/safety_engine.py"
    "aura_execution/safety/models/execution_risk.py"
    "aura_execution/safety/models/risk_level.py"
    "aura_execution/safety/models/safety_decision.py"
    "aura_execution/safety/analysis/risk_analyzer.py"
    "aura_execution/safety/analysis/impact_analyzer.py"
    "aura_execution/safety/analysis/unsafe_action_detector.py"
    "aura_execution/safety/gates/execution_safety_gate.py"
    "aura_execution/safety/gates/pre_execution_gate.py"
    "aura_execution/safety/gates/post_execution_gate.py"

    # Sandbox
    "aura_execution/sandbox/sandbox_engine.py"
    "aura_execution/sandbox/environments/sandbox.py"
    "aura_execution/sandbox/environments/isolated_environment.py"
    "aura_execution/sandbox/environments/resource_limits.py"
    "aura_execution/sandbox/policies/sandbox_policy.py"
    "aura_execution/sandbox/policies/filesystem_policy.py"
    "aura_execution/sandbox/policies/network_policy.py"
    "aura_execution/sandbox/lifecycle/sandbox_manager.py"
    "aura_execution/sandbox/lifecycle/cleanup.py"

    # Concurrency
    "aura_execution/concurrency/concurrency_engine.py"
    "aura_execution/concurrency/scheduling/execution_scheduler.py"
    "aura_execution/concurrency/scheduling/parallel_scheduler.py"
    "aura_execution/concurrency/scheduling/priority_scheduler.py"
    "aura_execution/concurrency/coordination/task_coordinator.py"
    "aura_execution/concurrency/coordination/lock_manager.py"
    "aura_execution/concurrency/coordination/resource_lock.py"

    # Transactions
    "aura_execution/transactions/transaction_engine.py"
    "aura_execution/transactions/models/transaction.py"
    "aura_execution/transactions/models/transaction_state.py"
    "aura_execution/transactions/models/transaction_step.py"
    "aura_execution/transactions/lifecycle/prepare.py"
    "aura_execution/transactions/lifecycle/commit.py"
    "aura_execution/transactions/lifecycle/abort.py"
    "aura_execution/transactions/compensation/compensating_action.py"
    "aura_execution/transactions/compensation/compensation_manager.py"
    "aura_execution/transactions/compensation/rollback_strategy.py"

    # Checkpoints
    "aura_execution/checkpoints/checkpoint_engine.py"
    "aura_execution/checkpoints/models/checkpoint.py"
    "aura_execution/checkpoints/models/checkpoint_state.py"
    "aura_execution/checkpoints/models/checkpoint_metadata.py"
    "aura_execution/checkpoints/storage/checkpoint_store.py"
    "aura_execution/checkpoints/storage/snapshot_store.py"
    "aura_execution/checkpoints/recovery/checkpoint_loader.py"
    "aura_execution/checkpoints/recovery/resume_manager.py"

    # Recovery
    "aura_execution/recovery/recovery_engine.py"
    "aura_execution/recovery/models/execution_failure.py"
    "aura_execution/recovery/models/recovery_strategy.py"
    "aura_execution/recovery/models/recovery_result.py"
    "aura_execution/recovery/classification/failure_classifier.py"
    "aura_execution/recovery/classification/transient_failure.py"
    "aura_execution/recovery/classification/permanent_failure.py"
    "aura_execution/recovery/strategies/retry_strategy.py"
    "aura_execution/recovery/strategies/fallback_strategy.py"
    "aura_execution/recovery/strategies/rollback_strategy.py"
    "aura_execution/recovery/strategies/escalate_strategy.py"

    # Validation
    "aura_execution/validation/validation_engine.py"
    "aura_execution/validation/preconditions/precondition_checker.py"
    "aura_execution/validation/preconditions/state_validator.py"
    "aura_execution/validation/results/result_validator.py"
    "aura_execution/validation/results/expected_state_validator.py"
    "aura_execution/validation/results/outcome_validator.py"
    "aura_execution/validation/consistency/execution_consistency.py"
    "aura_execution/validation/consistency/state_consistency.py"

    # Observation
    "aura_execution/observation/observation_engine.py"
    "aura_execution/observation/models/observation.py"
    "aura_execution/observation/models/execution_event.py"
    "aura_execution/observation/models/state_change.py"
    "aura_execution/observation/collection/observer.py"
    "aura_execution/observation/collection/event_collector.py"
    "aura_execution/observation/collection/state_observer.py"
    "aura_execution/observation/analysis/result_analyzer.py"
    "aura_execution/observation/analysis/deviation_detector.py"
    "aura_execution/observation/analysis/outcome_analyzer.py"

    # Execution state
    "aura_execution/execution_state/state_engine.py"
    "aura_execution/execution_state/models/execution_state.py"
    "aura_execution/execution_state/models/action_state.py"
    "aura_execution/execution_state/models/workflow_state.py"
    "aura_execution/execution_state/transitions/state_transition.py"
    "aura_execution/execution_state/transitions/transition_validator.py"
    "aura_execution/execution_state/transitions/transition_manager.py"

    # Budgets
    "aura_execution/budgets/budget_engine.py"
    "aura_execution/budgets/models/execution_budget.py"
    "aura_execution/budgets/models/cost_budget.py"
    "aura_execution/budgets/models/time_budget.py"
    "aura_execution/budgets/models/resource_budget.py"
    "aura_execution/budgets/tracking/budget_tracker.py"
    "aura_execution/budgets/tracking/budget_monitor.py"

    # Action genome
    "aura_execution/action_genome/action_genome.py"
    "aura_execution/action_genome/identity/action_fingerprint.py"
    "aura_execution/action_genome/identity/action_identity.py"
    "aura_execution/action_genome/identity/action_version.py"
    "aura_execution/action_genome/performance/action_statistics.py"
    "aura_execution/action_genome/performance/reliability.py"
    "aura_execution/action_genome/performance/historical_outcomes.py"
    "aura_execution/action_genome/lineage/action_lineage.py"
    "aura_execution/action_genome/lineage/action_evolution.py"

    # Flight recorder
    "aura_execution/flight_recorder/flight_recorder.py"
    "aura_execution/flight_recorder/events/execution_event.py"
    "aura_execution/flight_recorder/events/action_event.py"
    "aura_execution/flight_recorder/events/tool_event.py"
    "aura_execution/flight_recorder/events/recovery_event.py"
    "aura_execution/flight_recorder/storage/event_store.py"
    "aura_execution/flight_recorder/storage/execution_log.py"
    "aura_execution/flight_recorder/reconstruction/execution_reconstructor.py"
    "aura_execution/flight_recorder/reconstruction/state_reconstructor.py"

    # Replay
    "aura_execution/replay/replay_engine.py"
    "aura_execution/replay/snapshots/execution_snapshot.py"
    "aura_execution/replay/snapshots/state_snapshot.py"
    "aura_execution/replay/snapshots/environment_snapshot.py"
    "aura_execution/replay/runner/replay_runner.py"
    "aura_execution/replay/runner/execution_comparator.py"

    # Provenance
    "aura_execution/provenance/provenance_engine.py"
    "aura_execution/provenance/models/execution_provenance.py"
    "aura_execution/provenance/models/action_provenance.py"
    "aura_execution/provenance/models/tool_provenance.py"
    "aura_execution/provenance/graph/provenance_graph.py"
    "aura_execution/provenance/graph/provenance_node.py"
    "aura_execution/provenance/graph/provenance_edge.py"

    # Bridges
    "aura_execution/reasoning_bridge/reasoning_adapter.py"
    "aura_execution/reasoning_bridge/inputs/reasoning_result.py"
    "aura_execution/reasoning_bridge/inputs/confidence_adapter.py"
    "aura_execution/reasoning_bridge/inputs/safety_decision.py"

    "aura_execution/planning_bridge/planning_adapter.py"
    "aura_execution/planning_bridge/inputs/plan.py"
    "aura_execution/planning_bridge/inputs/planned_action.py"
    "aura_execution/planning_bridge/inputs/plan_constraints.py"
    "aura_execution/planning_bridge/conversion/plan_converter.py"
    "aura_execution/planning_bridge/conversion/action_converter.py"

    "aura_execution/memory_bridge/memory_adapter.py"
    "aura_execution/memory_bridge/retrieval/past_execution.py"
    "aura_execution/memory_bridge/retrieval/execution_retriever.py"
    "aura_execution/memory_bridge/retrieval/outcome_retriever.py"
    "aura_execution/memory_bridge/writing/outcome_writer.py"
    "aura_execution/memory_bridge/writing/execution_writer.py"
    "aura_execution/memory_bridge/writing/failure_writer.py"

    "aura_execution/learning_bridge/learning_adapter.py"
    "aura_execution/learning_bridge/signals/execution_success.py"
    "aura_execution/learning_bridge/signals/execution_failure.py"
    "aura_execution/learning_bridge/signals/recovery_feedback.py"
    "aura_execution/learning_bridge/strategy/execution_strategy.py"
    "aura_execution/learning_bridge/strategy/strategy_optimizer.py"
    "aura_execution/learning_bridge/strategy/reliability_learner.py"

    # Planning feedback
    "aura_execution/planning_feedback/feedback_adapter.py"
    "aura_execution/planning_feedback/models/execution_feedback.py"
    "aura_execution/planning_feedback/models/plan_deviation.py"
    "aura_execution/planning_feedback/models/plan_outcome.py"

    # Multi-agent
    "aura_execution/multi_agent/multi_agent_executor.py"
    "aura_execution/multi_agent/coordination/agent_executor.py"
    "aura_execution/multi_agent/coordination/task_dispatcher.py"
    "aura_execution/multi_agent/coordination/result_aggregator.py"
    "aura_execution/multi_agent/synchronization/agent_barrier.py"
    "aura_execution/multi_agent/synchronization/shared_state.py"

    # Telemetry
    "aura_execution/telemetry/metrics/execution_metrics.py"
    "aura_execution/telemetry/metrics/action_metrics.py"
    "aura_execution/telemetry/metrics/failure_metrics.py"
    "aura_execution/telemetry/metrics/recovery_metrics.py"
    "aura_execution/telemetry/logging/execution_logger.py"
    "aura_execution/telemetry/logging/structured_logger.py"
    "aura_execution/telemetry/monitoring/execution_monitor.py"
    "aura_execution/telemetry/monitoring/resource_monitor.py"
    "aura_execution/telemetry/monitoring/health_monitor.py"

    # Configuration
    "aura_execution/configuration/defaults/execution_defaults.py"
    "aura_execution/configuration/defaults/safety_defaults.py"
    "aura_execution/configuration/defaults/budget_defaults.py"
    "aura_execution/configuration/profiles/development.py"
    "aura_execution/configuration/profiles/production.py"
    "aura_execution/configuration/profiles/research.py"
    "aura_execution/configuration/settings.py"

    # API
    "aura_execution/api/http/routes.py"
    "aura_execution/api/http/execution_routes.py"
    "aura_execution/api/http/approval_routes.py"
    "aura_execution/api/http/recovery_routes.py"
    "aura_execution/api/schemas/api_request.py"
    "aura_execution/api/schemas/api_response.py"
    "aura_execution/api/schemas/api_error.py"
    "aura_execution/api/application.py"

    # Security / recovery / replay tests
    "tests/security/permission_tests.py"
    "tests/security/sandbox_tests.py"
    "tests/security/policy_tests.py"
    "tests/recovery/retry_tests.py"
    "tests/recovery/rollback_tests.py"
    "tests/recovery/checkpoint_tests.py"
    "tests/replay/replay_tests.py"
    "tests/property/action_properties.py"
    "tests/property/state_properties.py"
    "tests/property/execution_properties.py"

    # Benchmarks
    "benchmarks/execution/throughput.py"
    "benchmarks/execution/latency.py"
    "benchmarks/execution/reliability.py"
    "benchmarks/recovery/recovery_time.py"
    "benchmarks/recovery/recovery_success.py"
    "benchmarks/concurrency/parallel_efficiency.py"
    "benchmarks/end_to_end/plan_to_execution.py"
    "benchmarks/end_to_end/full_aura_loop.py"

    # Evaluation
    "evaluation/evaluators/execution_evaluator.py"
    "evaluation/evaluators/safety_evaluator.py"
    "evaluation/evaluators/recovery_evaluator.py"
    "evaluation/evaluators/reliability_evaluator.py"
    "evaluation/datasets/execution_cases.py"
    "evaluation/datasets/failure_cases.py"
    "evaluation/datasets/adversarial_cases.py"
    "evaluation/gates/safety_gate.py"
    "evaluation/gates/reliability_gate.py"
    "evaluation/gates/release_gate.py"

    # Examples
    "examples/basic_execution/execute_action.py"
    "examples/basic_execution/execute_plan.py"
    "examples/recovery/automatic_recovery.py"
    "examples/sandbox/sandboxed_execution.py"
    "examples/parallel/parallel_execution.py"
    "examples/full_pipeline/aura_execution_demo.py"

    # Documentation
    "docs/architecture/overview.md"
    "docs/architecture/execution_flow.md"
    "docs/architecture/integration.md"
    "docs/execution/action_lifecycle.md"
    "docs/execution/recovery.md"
    "docs/execution/checkpointing.md"
    "docs/execution/replay.md"
    "docs/security/permissions.md"
    "docs/security/sandboxing.md"
    "docs/security/safety_gates.md"
    "docs/evaluation/benchmarks.md"
    "docs/evaluation/release_policy.md"

    # Scripts
    "scripts/validate_architecture.py"
    "scripts/dependency_check.py"
    "scripts/benchmark.py"
    "scripts/evaluate.py"
    "scripts/replay.py"
    "scripts/security_check.py"
    "scripts/release_check.py"
)

# ------------------------------------------------------------
# CREATE DIRECTORIES
# ------------------------------------------------------------

Write-Host "[1/4] Creating directories..." -ForegroundColor Yellow

foreach ($Directory in $Directories) {
    $Path = Join-Path $Repo $Directory

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

# ------------------------------------------------------------
# CREATE PYTHON PACKAGE INITIALIZERS
# ------------------------------------------------------------

Write-Host "[2/4] Creating Python package initializers..." -ForegroundColor Yellow

$PythonDirectories = @(
    "aura_execution"
)

$PythonDirectories += $Directories | Where-Object {
    $_ -like "aura_execution/*"
}

foreach ($Directory in $PythonDirectories) {
    $InitPath = Join-Path (Join-Path $Repo $Directory) "__init__.py"

    if ($Force -or -not (Test-Path -LiteralPath $InitPath)) {
        New-Item -ItemType File -Path $InitPath -Force | Out-Null
    }
}

# ------------------------------------------------------------
# CREATE FILES
# ------------------------------------------------------------

Write-Host "[3/4] Creating files..." -ForegroundColor Yellow

$Created = 0
$Existing = 0

foreach ($File in $Files) {
    $Path = Join-Path $Repo $File
    $Parent = Split-Path -Parent $Path

    if (-not (Test-Path -LiteralPath $Parent)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }

    if (Test-Path -LiteralPath $Path) {
        $Existing++
        continue
    }

    New-Item -ItemType File -Path $Path -Force | Out-Null
    $Created++
}

# ------------------------------------------------------------
# ROOT DOCUMENTATION
# ------------------------------------------------------------

$Readme = @'
# AURA Execution

The AURA Execution Engine is responsible for safely translating executable
plans and actions into controlled runtime operations.

## Responsibilities

- Execution lifecycle
- Action preparation and dispatch
- Capability and tool resolution
- Permission and approval enforcement
- Safety analysis and execution gates
- Sandboxed execution
- Concurrency management
- Transactions and compensation
- Checkpointing and resume
- Failure classification and recovery
- State validation
- Observation
- Provenance
- Replay
- Telemetry
- Planning, reasoning, memory and learning integration

## Architectural rule

This repository must prioritize genuine functionality over file count.

Do not generate filler methods, artificial extension surfaces, duplicate
managers, numbered operations, or generic wrappers merely to increase code
volume.

Every implementation must have a clear responsibility and behavioral tests.
'@

Set-Content `
    -LiteralPath (Join-Path $Repo "README.md") `
    -Value $Readme `
    -Encoding UTF8

$GitIgnore = @'
.venv/
venv/
env/
__pycache__/
*.py[cod]
*.pyo
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
.env.*
!.env.example
.vscode/
.idea/
*.log
.DS_Store
Thumbs.db
'@

Set-Content `
    -LiteralPath (Join-Path $Repo ".gitignore") `
    -Value $GitIgnore `
    -Encoding UTF8

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

Write-Host "[4/4] Repository creation complete." -ForegroundColor Green
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host " AURA EXECUTION REPOSITORY CREATED" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository:" -NoNewline
Write-Host " $Repo" -ForegroundColor Cyan
Write-Host ""
Write-Host "Directories declared : $($Directories.Count)"
Write-Host "Files declared       : $($Files.Count)"
Write-Host "Files created        : $Created"
Write-Host "Files already existed: $Existing"
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "This script creates the repository structure only."
Write-Host "It deliberately does NOT generate fake 1500-line implementations."
Write-Host "Production code should be implemented according to each module's"
Write-Host "actual responsibility and then validated with tests."
Write-Host ""
Write-Host "Done." -ForegroundColor Green