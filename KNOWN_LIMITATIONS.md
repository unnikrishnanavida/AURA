# KNOWN LIMITATIONS

Honest list. Nothing here is silently papered over.

## Structural / auto-generated trees

- **`06_SOURCE_CODE/aura-memory`** — 5,095 of 5,338 Python files are malformed auto-generated
  scaffolding (bare-text first lines, unterminated strings, duplicated headers). It is NOT salvageable as
  real code and is NOT the runtime. The authoritative memory implementation is the tested
  `06_SOURCE_CODE/aura/src/aura/memory/` package. These files are preserved (not regenerated as fake
  code) and labelled HISTORICAL/BROKEN.
- **`06_SOURCE_CODE/aura-learning`** — 163 malformed generated files (duplicate `from __future__`
  headers mid-file, 83 KB template bodies). Same disposition: superseded by `aura/src/aura/learning/`.
- **`06_SOURCE_CODE/aura-sdk`** — the one broken file was a stub-generator (`_generate_aura_sdk_stubs.py`,
  escaped-newline damage); removed this session because its purpose (generating fake stubs) is contrary
  to the mission. The rest of the tree is real code.
- Several standalone trees (`aura-api`, `aura-core`, `aura-memory`, `aura-knowledge`, `aura-planning`,
  `aura-execution`, `aura-cloud`, `aura-desktop`, `aura-mobile`, `aura-reflection`, `aura-brain`,
  `aura-sdk`) are scaffolds or partial auto-generated trees. The canonical, tested implementations live
  in the integrated `aura/` package. They are documented (IMPLEMENTATION_STATUS.md) rather than
  bulk-regenerated.

## Functional / deployment limitations

- Persistence ships with **real adapters**: SQLite (`memory/sqlite_store.py`)
  and PostgreSQL (`memory/postgresql_store.py`, `api/distributed.py`,
  `observability/pg_backup.py`); Redis is not implemented. (Bullet corrected
  2026-09-25; it previously claimed no adapters shipped.)
- No Kubernetes manifests; Docker + compose are real, K8s is explicitly unvalidated.
- External provider SDK bindings are not shipped; the embedded deterministic provider is used by default.
- The API is a minimal HTTP service (health/ready/reason/replay/openapi); no auth middleware, streaming,
  or rate-limit backend is wired in (hooks exist).
- Replay is truthful about determinism: it distinguishes RECORDED vs RECONSTRUCTED state and does not
  claim deterministic replay across nondeterministic external dependencies.
- The embedded provider is structural (not omniscient); uncertainty-first reasoning will answer
  "I do not know" at 0.0 confidence when evidence is insufficient.

## Environment notes

- Local mypy may need pure-Python mode where Application Control blocks compiled mypyc binaries; CI on
  Linux is unaffected.
- `06_SOURCE_CODE/aura-reasoning` was renamed on disk to `aura-reasoning(2)` (pre-existing workspace
  change); git still tracks the old path as deletions. This is outside my edits and is noted for the
  user to reconcile if desired.
- Pre-existing uncommitted changes exist across the workspace (doc edits, removed zips, renames); I did
  not revert or commit them.
