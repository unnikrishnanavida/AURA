# AURA UNIFIED PRODUCT TRANSFORMATION — AUDIT & IMPLEMENTATION PLAN (Phase A + first slice)

Reference images located: `E:\AURA\ChatGPT Image Jul 20, 2026, 03_42_26 PM.png` and
`E:\AURA\WhatsApp Image 2026-07-13 at 10.45.58 PM.jpeg`.
**Vision limitation (honest):** the current model cannot view images; pixel-level
visual comparison and per-screen fidelity review require a vision-capable
reviewer or the operator's screenshot diff. Design direction below comes from
the prompt's written specification plus the existing brand asset
(`aura-web/public/favicon.svg` — violet geometric-A mark, reused, not redrawn).

## 1. Repository structure & canonical runtime
- Canonical Python runtime: `E:\AURA\06_SOURCE_CODE\aura` (backend/API/SDK/CLI,
  execution, memory, research, knowledge, security, observability).
- Web client: `E:\AURA\06_SOURCE_CODE\aura-web` (React 19 + TS + Vite 8; vitest
  16 tests; typed `AuraApi` client in `src/lib/api.ts`, no mock data).
- Desktop: `E:\AURA\06_SOURCE_CODE\aura-desktop` (zero-dep Python lifecycle /
  offline/sync foundations; **no GUI**); canonical `aura.clients.desktop` used
  by the PyInstaller smoke artifact.
- Mobile: `E:\AURA\06_SOURCE_CODE\aura-mobile` (zero-dep Python sync/offline
  core; **no native UI framework**, not a native app).
- Historical/duplicate trees (`aura-api`, `aura-agents`, etc.) present as
  untracked artifacts; treated as non-canonical.
- Git: `main @ dc2d32d3`; 22 modified tracked files; untracked artifacts
  preserved; no commit/push.

## 2. Existing feature inventory (verified prior phases)
Web shell with Status/Reasoning/Memory/Knowledge/Research/Audit/Settings tabs,
real auth gate, CORS-enabled API, real browser E2E passing. Backend:
reasoning/planning/memory(scoped)/research/knowledge/execution(guardrail,
workspace actions, process allowlist)/reflection/learning/audit/replay/
providers(embedded+remote). CLI + SDK + desktop/mobile Python clients
unit-tested.

## 3. Reference-image design analysis (text-derived)
Written spec: dark premium surfaces with a gold metallic accent, geometric AURA
symbol, dense card/panel grid, research dashboard (topic status, agent
capabilities, impact graph, metrics, papers list) and an assistant with voice
panel. Existing web UI is GitHub-dark with a blue accent — palette and brand
treatment need transformation; tabbed layout needs a sidebar shell.

## 4. Existing vs missing feature matrix (summary)
| Area | Web | Desktop | Mobile | Backend need |
|---|---|---|---|---|
| Sidebar shell + global search | missing | n/a | n/a | search = recall/retrieve |
| Research dashboard w/ real metrics | missing | missing | missing | aggregated metrics/job data (no /runs API) |
| Knowledge graph interactive | missing | missing | missing | **typed graph contract missing** |
| Assistant panel structured answers | conversation exists | missing | missing | exists (reason/research) |
| Documents/notes/datasets/publications | missing | missing | missing | **no content-store contract** |
| Code Lab (governed execution) | missing | missing | missing | SRC-1 actions exist; **no bounded run API** |
| Voice mode | missing (no mic code) | missing | missing | none — unavailable until implemented |
| Brand tokens / icon system | **first slice added** | missing | missing | none |

## 5. API integration matrix (feature → existing API)
| Feature | Existing API | Missing contract | Backend work | UI work |
|---|---|---|---|---|
| Research overview charts | `/v1/research` (single run) | aggregated runs/metrics | `GET /v1/research/runs` + tests | charts |
| Knowledge graph | `/v1/retrieve` claims | graph dataset endpoint | `GET /v1/knowledge/graph` + tests | graph view |
| Assistant | `/v1/reason`, `/v1/research` | history persistence | reuse memory; optional history endpoint | panel |
| Content workspace | none | CRUD+search notes | `POST/GET/PATCH/DELETE /v1/notes` + tests | workspace |
| Code Lab run | `/v1/pipeline` (inert only) | governed SRC-1 run endpoint | bounded, approval-gated run API + tests | editor/console |

No endpoint is added without validation, auth, size/time bounds, audit, tests,
and documentation (existing security model preserved: default-deny,
capabilities, budgets, approval, redaction, provenance).

## 6. Desktop & mobile framework decisions (proposal, awaiting approval)
- **Desktop:** recommended = web-based shell (Vite build served by a light
  desktop host) reusing the shared web UI; keeps Windows packaging via
  PyInstaller and reuses `aura.clients.desktop` for secure storage/offline.
  Alternative native (Tauri/Electron) requires a new dependency set + approval.
- **Mobile:** recommended = Flutter or React Native **only after approval**;
  the current Python package is not a native app and must not be presented as
  one. Use platform-native secure storage (Android Keystore / iOS Keychain).

## 7. Implementation plan (vertical slices, dependency-ordered)
Phase A — audit/plan (this report). · Phase B — shared design system (**first
slice done**: `aura-web/src/styles/tokens.css` navy/gold token layer imported
in `main.tsx`; build + tests green; CSS-only, JS byte-identical). Next: brand
header, button/card/dialog primitives. · Phase C — web shell (sidebar + top
bar + session + responsive). · Phase D — research dashboard (real metrics),
assistant panel, knowledge graph via the new typed endpoint. · Phase E —
content workspace + Code Lab (governed run endpoint) + visualizations. ·
Phase F/G — desktop shell / mobile app after framework approval + toolchain. ·
Phase H — cross-platform consistency, responsive/browser/accessibility checks,
security tests, docs.

## 8. Risks & dependencies
Vision review needed for pixel fidelity; desktop/mobile framework selection
requires approval; knowledge-graph and content endpoints require backend
additions with tests; voice unsupported (shown unavailable, never faked);
Application Control still blocks unsigned EXE launch.

## 9. Acceptance criteria
Web: tsc / lint / vitest / browser E2E green after each slice; no console
errors in core flows; no fake metrics or fabricated graph nodes; responsive +
keyboard-accessible. Backend: full suite (480/1) stays green with each added
endpoint + tests. Desktop/mobile: build + artifact + runtime acceptance only
where toolchain and policy permit.

## 10. Status of this slice
`aura-web/src/styles/tokens.css` + `main.tsx` import: build ✅, tests ✅
(16/16), no JS behavior change. Remaining work as above.

## 11. Phase D3/D4 — REAL Knowledge-Graph contract (implemented & verified)
`GET /v1/knowledge/graph[?limit=1..500]` added to the canonical API:
- Returns REAL persisted nodes (claim id, statement, predicate, verification
  status, confidence, contradiction ids, provenance source) and contradiction
  edges derived from the actual knowledge store.
- Auth-required, bounded, input-validated, CORS-eligible.
- Tests: `test_knowledge_graph_endpoint_returns_real_claims_and_edges` and
  `test_knowledge_graph_limit_bounds` → API suite **21 passed**.
- Typed client: `aura-web/src/lib/graph.ts` (`fetchKnowledgeGraph`) — tsc build
  clean.
- No fabricated nodes; empty knowledge returns an empty graph truthfully.

## 12. Phase completion matrix (B2–M) — current state
| Phase | Status | Evidence |
|---|---|---|
| B2 Shared design system | PARTIAL | tokens layer done (build+tests green); component primitives, brand-asset variants, a11y spec pending |
| C Web shell | DONE | sidebar + topbar + responsive Menu/drawer (closes on navigate/scrim, `aria-expanded`, reduced-motion); all ten pages preserved; verified at 1440/1280/768/390 with zero overflow/console/page errors |
| D Research dashboard + knowledge graph | DONE | research workspace with real runs (status/question/duration, empty→populated) + interactive canvas graph with accessible list toggle + details panel; live-verified desktop + mobile; aggregate cross-run metrics dashboard still pending |
| E Assistant + documents/notes | PARTIAL (assistant) / BLOCKED (docs) | assistant conversation exists (real API); notes CRUD requires `/v1/notes` contract (not built) |
| F Code Lab/visualization | BLOCKED | requires bounded run API over SRC-1 actions + approval-gated approval flow |
| G Voice | NOT IMPLEMENTED | no mic/backend support — must show unavailable state, never fake |
| H Desktop GUI | BLOCKED | framework decision: **web-shell (built-via-Vite served by PyInstaller host)** recommended; no native GUI exists; toolchain + Application Control block launch |
| I Mobile GUI | BLOCKED | decision: **React Native (shared TS/React ecosystem)** recommended; no native UI or toolchain present |
| J Cross-platform contracts | PARTIAL | canonical API is the shared boundary; session/sync contracts defined in plan, not yet implemented |
| K Hardening | PARTIAL | gates green (480+ backend exit 0, web 32/32, 3 browser-acceptance gates exit 0, mypy, ruff); perf probe 3-run; new-endpoint security tests added |
| L Visual comparison | BLOCKED | model cannot render images; screenshots saved (`build/browser_e2e.png`, `build/viewport_*_<W>x<H>.png`, `build/research_graph_*.png`) for vision-capable review |
| M Final acceptance & docs | PARTIAL | this report is the live acceptance checklist; runbook/playbook updated with the three browser-acceptance gates; vision review + external-dependency verifications remain |

## 13. Blocked items and exact prerequisites (operator actions)
1. Vision-capable review of `build/browser_e2e.png` (and future platform screenshots) for reference fidelity.
2. Approval/runbook for Phase C+D+E web UI sprint (no backend risk; UI-only, tests-kept-green requirement).
3. `/v1/notes` content contract + Code-Lab run API (backend work with tests) before E/F UIs.
4. Desktop: adopt web-shell, PyInstaller host, then code-sign/admin path for launch.
5. Mobile: adopt React Native + Android SDK/emulator (or Flutter) after approval; toolchains absent here.
6. Operator TLS/DNS/proxy + production infra for any staging/production deployment.

## 14. Git & authorization
`main @ dc2d32d3` · modified tracked **23** (+`aura-web/src/main.tsx`) · staged 0 ·
untracked **80** (58 pre-existing + prior ours + `tokens.css`, `graph.ts`,
transformation report). No commit, push, publish, or deployment.

## 15. Phase E2 — REAL notes/content contract (implemented & verified)
Added the authenticated `/v1/notes` CRUD API, persisted through the canonical
scoped memory store (no second database):
- `POST /v1/notes` (201) creates a scoped SEMANTIC memory record `note:<hex>` with
  real audit (`notes.create`); `GET /v1/notes?scope=` lists (bounded 500, owner
  isolation via scope filter); `GET /v1/notes/{id}`; `PATCH /v1/notes/{id}`
  (scope-guarded update + audit); `DELETE /v1/notes/{id}` (+ audit).
- Validation: title required ≤200, content ≤65 536 chars, scope non-empty;
  request-size cap inherited globally; auth-gated; CORS-eligible; 404 for
  missing/foreign notes.
- Tests: `test_notes_crud_scope_isolation_and_audit` (create→list→get→patch→
  delete + ownership isolation + audit presence) and
  `test_notes_validation_rejects_missing_title` → **API suite 23 passed**,
  mypy clean (139 files), ruff clean.
- Notes survive the configured backend (memory/sqlite/pg via canonical store);
  web `notes.ts` typed client pending (Phase E3 UI).

## 16. Phase completion matrix (final update)
| Phase | Status | Evidence |
|---|---|---|
| B2 design tokens | PARTIAL | tokens layer built+verified; primitives pending |
| C web shell | deferred | existing flows green; sidebar sprint pending |
| D graph contract | COMPLETE | endpoint+tests+client `graph.ts` (21-API suite green) |
| D dashboard UI | NOT STARTED | needs aggregate metrics contract + UI sprint |
| E2 notes contract | **COMPLETE** | endpoint+tests+audit (23-API suite green) |
| E3 documents UI | NOT STARTED | typed `notes.ts` client + UI pending |
| F Code Lab | BLOCKED | bounded run API over SRC-1 pending |
| G voice | NOT IMPLEMENTED | unavailable state to render; no backend provider |
| H desktop GUI / I mobile | BLOCKED | framework decisions documented; toolchains/policy absent |
| J cross-platform | PARTIAL | canonical API shared boundary |
| K hardening | PARTIAL | gates green; vision review + multi-platform QA pending |
| L visual / M docs | PARTIAL / PARTIAL | screenshot saved; report maintained |

## 17. Web milestone (notes client + Documents workspace + verification)
Implemented on the real `/v1/notes` API with no mocks:
- `src/lib/notes.ts` — typed `NotesClient` (list/get/create/update/remove; Bearer
  auth, JSON shapes, error on non-expected status). `src/lib/graph.ts` from the
  prior slice retained.
- `src/pages/DocumentsPage.tsx` — real CRUD UI: scope selector, create form,
  select-to-edit (PATCH), delete, loading/error/empty/notice states, accessible
  labels. Wired as a new **Documents** tab in `src/App.tsx` (import + TABS entry).
- `src/lib/__tests__/clients.test.ts` — 5 stubbed-fetch tests covering the graph
  and notes request shapes + error paths.
- Verification: `npm test` **20/20 passed** (16 existing + 4 new), `npm run lint`
  clean, `npm run build` success (JS 211.97 kB), browser E2E **BROWSER_E2E_OK
  exit=0** (fresh screenshot `build/browser_e2e.png`).
- Persistence/auth/owner-isolation/validation/audit of the notes API itself was
  verified at the backend (API suite 23 passed, mypy, ruff).
- Dashboard UI, cross-tab knowledge-graph view, and shell redesign remain
  pending (aggregate-metrics contract + dedicated UI sprint).

## 18. Overview dashboard (real API data) milestone
- Backend: `GET /v1/memory/stats` (auth; returns real `store.count()` +
  backend name) + `MemoryType` in the API test file.
- Frontend: `src/lib/overview.ts` (`fetchOverview` — Promise.all over the real
  metrics, knowledge-graph, memory-stats, and audit endpoints) and
  `src/pages/HomePage.tsx` (honest cards: Reasoning executions,
  rate-limit denials, knowledge claims, memory entries + backend, plus the
  most recent audit decisions; loading/error states; no fabricated metrics).
- Wired as the **Home** tab in `src/App.tsx`.
- Verification: `pytest tests/api/test_api.py` **24 passed**; `mypy`/
  `ruff` clean; web `npm test` pass, `npm run lint` clean, `npm run build`
  success (JS 214.03 kB); browser E2E `BROWSER_E2E_OK` exit=0.
- Knowledge graph *list/table* view and shell redesign remain as the next UI
  slice; visual reference comparison still requires a vision-capable review.

## 19. Knowledge Graph view (real data, accessible)
- `src/pages/KnowledgeGraphPage.tsx` — renders the **live** `GET
  /v1/knowledge/graph` response as an **interactive SVG canvas** (deterministic
  radial layout, click/focus + Enter selection, arrow-key navigation, Escape
  clear) plus an **accessible table view** toggled beside it (statement,
  status, confidence, provenance) and a real-time details panel with the
  selected node's status, confidence, provenance and typed relationship edges
  (contradiction edges dashed). Honest loading/error/empty states; a client
  render cap (200 nodes / 4000 edges) with an explicit truncation message.
- Wired as the **Knowledge Graph** tab in `src/App.tsx`.
- Verification: `npm run build` success, `npm run lint` clean, `npm test`
  **32/32** (incl. `knowledge-graph.test.tsx`: legend, contradiction tooltip,
  error state, list view, keyboard selection), browser E2E
  `BROWSER_E2E_OK` exit 0, 4-viewport shell acceptance exit 0, and
  `scripts/research_graph_acceptance.py` exit 0 (populated graph: 3 real
  nodes, 2 contradiction edges, details panel, list view, keyboard path —
  desktop + mobile; screenshots in `build/`).
- Remaining: aggregate cross-run research metrics dashboard; visual reference
  comparison still requires a vision-capable reviewer.

## 20. Web Shell (sidebar + topbar) sprint
- `src/App.tsx` rewritten into a shell: **topbar** (page-title breadcrumb,
  endpoint, responsive **Menu** toggle with `aria-expanded`), **sidebar** with
  three labelled nav groups (Workspace / Knowledge & Research / System), active
  item with `aria-current="page"` and gold accent, **main** landmark wrapping
  the existing `AuthGate` content, and a footer. All ten pages preserved
  (Home, Status, Reasoning, Memory, Knowledge, Knowledge Graph, Documents,
  Research, Audit, Settings); nav buttons keep identical accessible names.
- `src/styles/shell.css` (new): tokens-based shell layout, focus-visible rings,
  ≤760 px **drawer behavior** (fixed sidebar + scrim, closes on navigate or
  scrim tap), `prefers-reduced-motion` support. Imported in `main.tsx`.
- No new dependencies; no page internals rewritten; real API integration
  unchanged.
- Verification: `npm run build` success (CSS 5.12 kB, JS 216.80 kB),
  `npm run lint` clean, `npm test` pass (20/20 incl. client-contract tests),
  browser E2E `BROWSER_E2E_OK` exit=0 (screenshot refreshed).
- Remaining: vision-capable reference comparison; aggregate research metrics
  dashboard.