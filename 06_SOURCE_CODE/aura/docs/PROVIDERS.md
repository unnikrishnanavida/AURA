# AURA Providers

The provider runtime (Phase 29) is a real, policy-enforced boundary between
reasoning and model providers.

## Canonical pieces

- `aura.providers.base.Provider` — contract: `name`, `profile` (capabilities,
  cost, latency, reliability, privacy/local flags), `timeout_seconds`,
  `health()`, `reason(question, **kwargs)`.
- `aura.providers.base.ProviderRegistry` — the ONE registry of profiles and
  runtime instances; deterministic policy-filtered selection.
- `aura.providers.manager.ProviderManager` — the single dispatch/synthesis
  boundary; policy (privacy/cost/local/capability), timeout, usage counters,
  `provider_failure` emission (metrics+audit), health aggregation.
- `aura.providers.embedded.EmbeddedReasoningProvider` — always registered,
  deterministic/local, never used for synthesis (no recursion).
- `aura.providers.remote.HttpChatProviderAdapter` — OpenAI-compatible
  `/chat/completions` and Ollama `/api/chat`; credential-safe, injectable
  transport.

## Configuration

```env
AURA_PROVIDER_ENABLED=0            # 1 to enable remote synthesis
AURA_PROVIDER_KIND=openai          # openai | ollama
AURA_PROVIDER_BASE_URL=            # e.g. https://api.openai.com/v1
AURA_PROVIDER_MODEL=
AURA_PROVIDER_API_KEY=             # SecretStr; never logged
AURA_PROVIDER_TIMEOUT_SECONDS=15
AURA_PROVIDER_PRIVACY_APPROVED=0   # 1 to allow policy-selected remote calls
```

## Behavior

- Default (no provider configured): fully deterministic multi-strategy
  reasoning plus Step 1A grounded context; no external dependency. When
  reasoning and grounding both decline, the response carries
  `abstention_reason` explaining that no language model is configured — it is
  never a bare, unexplained "I do not know".
- Routing is deterministic and explainable:
  `local deterministic -> grounded context -> authorized provider -> abstention`.
  A provider is consulted **only** when deterministic reasoning and grounding
  both fall short; it is never called just because one is registered.
- With a policy-approved generation provider, the provider receives the
  **Step 1A bounded context** (system policy, user request, authorized context
  with provenance, task) and may compose an answer. Model output is reported
  with `verified: false` and is never promoted to verified truth.
- Contested/insufficient/uncertain deterministic outcomes are never overridden.
- Failures map to a closed taxonomy (`ok`, `not_configured`, `unauthorized`,
  `unavailable`, `model_unavailable`, `authentication_failed`, `forbidden`,
  `timeout`, `cancelled`, `rate_limited`, `transient_failure`,
  `malformed_response`, `unsupported_capability`, `budget_exceeded`), each
  recorded with `provider_failure` metrics, `provider.*` audit entries and
  usage counters. A failing provider never crashes a request.

## Discovery

`GET /v1/providers` (scope `providers.read`) reports, per provider and without
any credential material: `registered`, `configured`, `available`, `supported`,
`selected`, model id, locality, privacy approval and budgets. A registered
adapter is not a configured model, and neither is evidence one is running.

## Authorization

Using a language model requires the `providers.use` scope, checked at the API
boundary and threaded to the provider boundary. A credential may reason from
saved memory while being refused model access; that returns
`403 api.provider_forbidden`, never a silent fallback.

## Honest status

- Embedded provider: **IMPLEMENTED + LIVE** (deterministic, local, no network).
- `HttpChatProviderAdapter` (OpenAI-compatible + Ollama): **IMPLEMENTED +
  UNIT TESTED + RUNTIME VERIFIED against a local OpenAI-compatible endpoint**.
- **Live external-provider verification: NONE** — no operator credentials or
  hosted endpoint were available. No external or paid call has been made.
- **No local model ships with AURA.** `11_MODELS/` contains one README and no
  weights; an Ollama or OpenAI-compatible endpoint must be operator-configured.
- **Streaming: NOT IMPLEMENTED.** Requests send `stream: false` and a single
  response is awaited. A correct non-streaming path was preferred over a partial
  streaming subsystem. Follow-up.
- **Embeddings / semantic retrieval: NOT IMPLEMENTED.** Retrieval is lexical
  only, so a saved fact with no token overlap with the question will not be
  recalled ("deadline is next Friday" is not retrieved for "what should I work
  on today?"). This is a known capability gap, not a hidden heuristic.
- **Cancellation is partial.** The token is checked before dispatch, on
  provider-raised cancellation, and after the response returns; an in-flight
  HTTP call is bounded by its configured timeout rather than aborted
  mid-flight. Slice 1D should complete this.
