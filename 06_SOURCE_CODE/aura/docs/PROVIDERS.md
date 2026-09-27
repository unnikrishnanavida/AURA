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
  reasoning; no external dependency.
- With a policy-approved synthesis provider: after consensus + verification of
  an evidence-backed outcome, the provider receives **conclusions +
  verification only** (never hidden chain-of-thought) and may polish the final
  answer. Contested/insufficient/uncertain results are never overridden.
- Failures: provider errors/timeouts/malformed responses are recorded
  (`provider_failure`, audit `provider.*`, usage counters) and the
  deterministic answer is returned — requests never crash.

## Honest status

- Embedded provider: **IMPLEMENTED + LIVE** (deterministic).
- Remote adapters: **IMPLEMENTED + UNIT TESTED** (injected transport);
  **LIVE VERIFICATION: NONE** — no operator credentials/endpoints were
  available during development. Live calls require operator configuration and
  re-verification.