# AURA Testing Guide

## Canonical runtime test suite

`06_SOURCE_CODE/aura/tests` covers: foundation, config, core, security, memory,
knowledge, reasoning, planning, execution, reflection, learning, observability,
providers, brain, sdk, api, agents bridge. All currently pass.

## Behavior-focused guidance

- Prefer behavioral tests over shell/reflection tests.
- Cover failure cases (denials, timeouts, budget exhaustion, contradictions,
  insufficient evidence, authorization failures).
- Do not write tests merely to raise the count; every test must assert real
  behavior.

## Real-test evidence (final pass)

| Repo | Tests | Result |
|---|---|---|
| aura (canonical) | full suite | passed |
| aura-agents | 92 | passed |
| aura-research | 3 | passed |
| aura-security | 9 | passed |
| aura-execution-complete | 2 | passed |
| aura-cloud | 2 | passed |
| aura-desktop | 2 | passed (after shadow fix) |
| aura-mobile | 2 | passed (after shadow fix) |
| aura-core | 6 | passed (new behavioral tests) |

## Repos without runnable tests yet

- aura-api, aura-cli: test files are scaffolds (0 runnable).
- aura-knowledge: test files are scaffolds.
- aura-reflection: tests are scaffold-only.
- aura-planning, aura-execution: tests exist but import `.planning/.execution`
  package names not wired in the flat layout (documented limitation).