# AURA Component Boundaries

## Canonical `aura/` package boundaries

Each subpackage has an explicit responsibility and dependency direction. No
subpackage imports downward into clients; the flat import graph has no cycles.

| Subpackage | Owning concern | Depends on |
|---|---|---|
| foundation | ids, errors, Result, clocks, lifecycle, cancellation, RNG | stdlib only |
| config | typed settings, loader (defaults->file->env) | foundation |
| core | bootstrap, DI container, registry, lifecycle manager, health | foundation, config |
| memory | episodic/semantic/working/procedural, provenance, graphs | foundation |
| knowledge | claims/evidence/sources, trust, contradictions | foundation |
| reasoning | strategies, consensus, verification, uncertainty | foundation, knowledge |
| planning | goals, decomposition, risk, comparison | foundation |
| execution | actions, world-state vs action-input, checkpoints | security |
| reflection | post-execution review, counterfactuals | foundation |
| learning | validated signals, versioning, rollback, auth gate | security |
| brain | cognitive orchestration (bounded loop) | memory..learning |
| security | capabilities, permissions, safety, budgets, recovery, audit | foundation |
| observability | logging, metrics, flight recorder, replay, provenance | foundation |
| providers | provider registry + embedded provider | foundation |
| research | ledger, claim passport, evidence provenance | knowledge |
| sdk | typed public client `from aura import Aura` | brain |
| api | thin HTTP routes | sdk/services |
| cli | developer commands | sdk/api |

## Standalone engine boundaries

- `aura-agents` — guarded execution loop; capability/permission/safety/budget
  checks; flight recorder; delegation. Not imported by canonical runtime except
  via the optional `aura/agents` bridge.
- `aura-research`, `aura-security`, `aura-execution-complete` — independently
  tested engines with their own clear ownership of their niche.
- `aura-cloud`, `aura-desktop`, `aura-mobile` — client-side/platform
  architectures that call into services; they must not reimplement core
  intelligence.
- `aura-planning`, `aura-execution` (standalone trees) — flat-layout real code
  whose tests reference a package name (`aura_planning`/`aura_execution`) that is
  not yet wired; canonical planning/execution lives in `aura/`.
- `aura-api`, `aura-cli` — compatibility/interface layers, scaffold-heavy.
- `aura-knowledge`, `aura-reflection` (standalone trees) — predominantly
  scaffolds; canonical implementations live in `aura/`.

## No-sharing rules

- No hidden global mutable state across engines.
- No multiple competing ID/error/clock systems: canonical `aura/foundation`
  is authoritative.
- Clients never import engines directly; they go through the canonical SDK.
- Standalone engines never import clients (no circular direction).