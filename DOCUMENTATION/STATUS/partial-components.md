# Partial Components

Components with real authored code that are not yet complete enough to be
canonical runtime:

| Component | What is real | What is missing |
|---|---|---|
| aura-core | kernel lifecycle, subsystem modules | functional overlap with aura/foundation; needs packaging alignment |
| aura-cloud | control plane, policy gates, simulator, canary/rollback (2 tests) | real provider SDKs, full deployment profiles |
| aura-desktop | app lifecycle, capability gate (2 tests) | native packaging, plugins, IPC end-to-end |
| aura-mobile | permission broker, sync queue (2 tests) | native packaging, offline sync end-to-end |
| aura-planning | 429 real flat modules | package wiring so tests run; consolidation with aura/planning |
| aura-execution | 426 real flat modules | package wiring so tests run; consolidation with aura/execution |
| aura-api | auth, rate-limit, resilience, jobs, gateway modules | 61% scaffold; tests scaffold |
| aura-cli | formatters, security, diagnostics | 79% scaffold; tests scaffold |
| aura-reflection | 56 real modules | 74% scaffold; tests scaffold |

These are preserved and documented; the canonical `aura/` runtime is the
supported integration path.