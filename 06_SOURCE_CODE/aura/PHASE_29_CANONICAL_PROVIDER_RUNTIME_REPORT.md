# Phase 29 — Canonical Provider Runtime Integration Report

**Status:** COMPLETE. Commit: `feat(phase29)`. The canonical reasoning path
now **genuinely enters the provider boundary**. mypy strict clean; ruff clean;
all affected suites pass.

---

## 1. Previous state (inspection)

- `providers/` contained a dead abstraction: `ProviderProfile`/`ProviderRegistry`
  (profiles only) and `EmbeddedReasoningProvider` (wraps `ReasoningEngine`)
  — but **nothing routed through them**: `ReasoningEngine` had zero provider
  references; `BrainEngine` constructed it directly. `provider_failure` was a
  documented-but-uninstrumented metric (Phase 26 report).

## 2. What was built

| Module | Change |
|--------|--------|
| `providers/base.py` | Canonical `Provider` contract (name/profile/timeout/health/reason); **ONE** `ProviderRegistry` extended to hold runtime **instances** + default; `ProviderPolicy` + `ProviderUsage` |
| `providers/errors.py` (new) | `ProviderError`/`ProviderTimeoutError`/`ProviderUnavailableError`/`MalformedProviderResponse`/`ProviderPolicyError` |
| `providers/manager.py` (new) | `ProviderManager`: policy-filtered selection, usage counters, health aggregation, `snapshot()`, and the **single `synthesize()` dispatch** that emits `provider_failure` exactly once per boundary failure (metrics + audit + usage) |
| `providers/remote.py` (new) | Real HTTP adapters: OpenAI-compatible `/chat/completions` + Ollama `/api/chat`; credential-safe; **transport-injectable** so the full request/parse/error path is unit-tested with no live endpoint |
| `providers/embedded.py` | Conforms to the contract; deliberately does **not** claim `reasoning.synthesis` (no self-recursion) |
| `reasoning/engine.py` | Optional `provider_manager`; after consensus+verification, consults the manager for **safe structured synthesis** — only when the deterministic outcome is evidence-supported (contested/insufficient/uncertain results are never overridden, preserving uncertainty-first); result carries `provider_name`/`provider_synthesized` |
| `brain/engine.py` | `create()` builds the manager from config (injectable for tests); stores `brain.provider_manager`; `BrainResult.summary()` exposes provider metadata |
| `config/settings.py` + `.env.example` | `ProviderConfig` (`enabled/kind/base_url/model/api_key/timeout/privacy_approved`); API key is `SecretStr`, redacted in `model_dump_safe`; `AURA_PROVIDER_*` env mapping |

## 3. Security properties

- **No credentials logged** — API keys are `SecretStr` and appear only in the
  Authorization header; safe dumps redact.
- **No silent privacy bypass** — default policy requires `privacy_approved=True`;
  a remote provider without it is registered but **never selected**.
- **No hidden chain-of-thought** — the provider receives only safe structured
  context (question + conclusions + verification), never reasoning traces.
- **No unsafe autonomous override** — a provider may only polish evidence-backed
  answers; `I do not know`/CONTESTED outcomes are authoritative.
- **fail-safe dispatch** — provider errors/timeouts/malformed responses return
  `None` (deterministic fallback), never propagate, and are recorded.

## 4. Test matrix (§29.8)

Unit tests (mocks/injected transports): success path · no-matching-provider ·
provider error → `provider_failure` + audit + fallback · timeout recorded ·
policy (privacy) rejection · health aggregation · config build (disabled/
enabled/redaction) · remote openai request shape + context forwarding ·
HTTP 500 · malformed JSON · missing content · timeout mapping · ollama flavor ·
health ok/down · reasoning consults provider · deterministic default unchanged ·
uncertainty-first not overridden · failure falls back · brain end-to-end ·
embedded-not-used-for-synthesis.

## 5. Runtime verification (real, local)

- **Provider path:** local HTTP chat-endpoint (stdlib server, port 0) served an
  OpenAI-format response. Through `Aura → Brain → Reasoning → ProviderManager →
  adapter → HTTP`, the answer was `runtime synthesized answer`, model seen by
  the server (`test-model`), `provider_call=1`, and the summary carried
  `provider: {name: live-test, synthesized: true}`.
- **Failure path:** same canonical path against a closed endpoint → deterministic
  fallback answer, `provider_failure=1`, no provider metadata.
- **Live external-provider verification: NOT VERIFIED** — no operator-supplied
  OpenAI/Anthropic/Gemini/Groq credentials or Ollama instance were available;
  adapters are contract-implemented and unit-tested, flagged
  `UNIT TESTED / LIVE: NOT VERIFIED`.

## 6. Known limitations / classifications

- External provider live calls: **NOT VERIFIED** (no credentials/infrastructure).
- `HttpChatProviderAdapter` implements OpenAI-compatible + Ollama chat only;
  other providers require the same adapter pattern (documented).
- Synthesis consults the provider only when a provider is configured with the
  synthesis capability and policy-approved; default behavior is unchanged.