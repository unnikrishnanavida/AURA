# AURA Ecosystem Architecture (Phase 5–8)

```mermaid
flowchart TD
    subgraph Clients
        WEB[aura-web: React API client]
        SDK[aura-sdk: Local + HTTP transports]
        CLI[aura-cli]
    end

    subgraph Canonical["06_SOURCE_CODE/aura — ONE canonical runtime"]
        API[AuraApiServer: auth, reason, memory, knowledge, research, plan, metrics, audit, replay, pipeline]
        BRAIN[BrainEngine: orchestration]
        PIPE[ExecutionPipeline: canonical request flow]

        subgraph Cognition
            MEM[memory: types, confidence, provenance, sensitivity, retention, lifecycle]
            KNW[knowledge: claims, evidence, trust, contradictions]
            RSN[reasoning: 6 strategies, consensus, verification, calibration]
            RSR[research: epistemic ledger, passports]
            PLN[planning: decompose, risk, alternatives]
            REF[reflection: outcomes, lessons, counterfactuals]
            LRN[learning: gate + loop, versioned registry, rollback]
        end

        subgraph Execution
            EXE[execution: timeout, retry, idempotency, WorldState]
            SEC[security: guardrails, capabilities, policies, budgets]
            DEF[adaptive defense: evidence → propose → sandbox → approve → canary]
        end

        OBS[observability: metrics, flight recorder, provenance, replay, audit]
    end

    subgraph Historical
        HM[aura-memory / aura-learning / aura_reasoning / aura-reasoning(2)]
    end

    AGENTS[aura-agents: protocols + CanonicalMemoryProvider]

    WEB -->|HTTP| API
    SDK -->|HTTP| API
    SDK -->|in-process| PIPE
    CLI --> BRAIN
    API --> BRAIN
    PIPE --> MEM & KNW & RSR & RSN & PLN & SEC & EXE & REF & LRN & OBS
    BRAIN --> MEM & KNW & RSN & PLN & REF & LRN & OBS
    AGENTS -->|MemoryProvider| MEM
    EXE --> SEC
    HM -. classified .-> MEM
```

## Dependency direction

```
interfaces      (contracts, provider protocols)
   ↓
application     (SDK, web, CLI)
   ↓
orchestration   (BrainEngine, ExecutionPipeline)
   ↓
domain          (memory, knowledge, reasoning, planning, ...)
   ↓
infrastructure  (transport, persistence, providers)
```

The canonical runtime remains the single source of truth. `aura-sdk`,
`aura-web`, `aura-agents`, and the historical trees integrate through
contracts/adapters (HTTP API, `MemoryProvider`, recovery-analysis) and never
duplicate the core engines.