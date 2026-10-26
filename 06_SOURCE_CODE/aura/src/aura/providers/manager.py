"""Canonical provider manager.

The single runtime boundary between reasoning and model providers:

- policy-filtered selection via the ONE :class:`ProviderRegistry`;
- one dispatch path (:meth:`synthesize`) through which the reasoning engine
  consults a generation/synthesis provider with *safe structured context*
  (conclusions + verification only — never hidden chain-of-thought);
- the **one place** where ``provider_failure``-class signals are emitted
  (metrics + audit + usage counters); failures never crash the request — the
  caller falls back to the deterministic path;
- health aggregation and usage introspection for observability.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Sequence
from typing import Any

from aura.config.settings import AuraConfig
from aura.foundation.cancellation import CancellationToken
from aura.foundation.errors import CancelledError
from aura.providers.base import (
    Provider,
    ProviderPolicy,
    ProviderProfile,
    ProviderRegistry,
    ProviderUsage,
)
from aura.providers.errors import (
    MalformedProviderResponse,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from aura.providers.result import (
    RETRYABLE_STATUSES,
    ProviderCapability,
    ProviderDescriptor,
    ProviderResult,
    ProviderState,
    ProviderStatus,
)
from aura.providers.result import (
    ProviderUsage as ProviderCallUsage,
)


def build_provider_manager(cfg: AuraConfig, *, metrics: Any = None, audit: Any = None) -> Any:
    """Build a :class:`ProviderManager` from validated configuration.

    When ``cfg.provider`` is not enabled this returns ``None`` (the default
    deterministic path). Remote providers are only constructed from explicit
    configuration; the embedded provider is always registered so registry
    discovery works even without remote credentials.
    """
    provider_cfg = cfg.provider
    if provider_cfg is None or not provider_cfg.enabled:
        return None
    manager = ProviderManager(metrics=metrics, audit=audit)

    from aura.providers.embedded import EmbeddedReasoningProvider

    manager.register(EmbeddedReasoningProvider(seed=cfg.engines.reasoning_seed))

    if provider_cfg.kind in {"openai", "ollama"} and provider_cfg.base_url and provider_cfg.model:
        from aura.providers.remote import HttpChatProviderAdapter

        manager.register(
            HttpChatProviderAdapter(
                name=provider_cfg.name,
                base_url=provider_cfg.base_url,
                model=provider_cfg.model,
                api_key=provider_cfg.api_key.get_secret_value() if provider_cfg.api_key else None,
                timeout_seconds=provider_cfg.timeout_seconds,
                flavor=provider_cfg.kind,
                privacy_approved=provider_cfg.privacy_approved,
            )
        )
        if provider_cfg.name:
            manager.registry.set_default(provider_cfg.name)
            manager._configured_name = provider_cfg.name  # noqa: SLF001 - same module
    return manager


#: Operator-facing reasons for "no provider ran". These are deliberately
#: specific: "no provider is configured" and "the configured provider is not
#: approved for this data" are different problems with different fixes.
_NO_PROVIDER_REASON: dict[ProviderStatus, str] = {
    ProviderStatus.NOT_CONFIGURED: (
        "no language model provider is configured; AURA can still reason over "
        "saved memory and stored knowledge"
    ),
    ProviderStatus.UNAUTHORIZED: (
        "the configured provider is not approved for this data under the active privacy policy"
    ),
    ProviderStatus.BUDGET_EXCEEDED: "every provider exceeded the configured cost or latency budget",
    ProviderStatus.UNAVAILABLE: "the configured provider is not currently reachable",
    ProviderStatus.UNSUPPORTED_CAPABILITY: "no configured provider supports this kind of request",
}


def profile_health(registry: ProviderRegistry, name: str) -> bool:
    """Health of a registered runtime instance, or False when absent."""
    try:
        return bool(registry.get_instance(name).health())
    except Exception:  # noqa: BLE001 - a missing or broken probe is not healthy
        return False


def _status_for(exc: Exception) -> ProviderStatus:
    """Map one boundary failure onto the canonical outcome taxonomy.

    HTTP status decides between "rejected" and "broken": a 401 is an
    authentication failure the operator can fix, a 503 is a transient outage
    worth retrying, and neither is the same event as a timeout.
    """
    if isinstance(exc, ProviderTimeoutError):
        return ProviderStatus.TIMEOUT
    if isinstance(exc, MalformedProviderResponse):
        return ProviderStatus.MALFORMED_RESPONSE
    if isinstance(exc, CancelledError):
        return ProviderStatus.CANCELLED
    http_status = getattr(exc, "http_status", None)
    if http_status == 401:
        return ProviderStatus.AUTHENTICATION_FAILED
    if http_status == 403:
        return ProviderStatus.FORBIDDEN
    if http_status == 404:
        return ProviderStatus.MODEL_UNAVAILABLE
    if http_status == 429:
        return ProviderStatus.RATE_LIMITED
    if http_status is not None and 500 <= int(http_status) < 600:
        return ProviderStatus.TRANSIENT_FAILURE
    if isinstance(exc, ProviderUnavailableError):
        return ProviderStatus.UNAVAILABLE
    return ProviderStatus.TRANSIENT_FAILURE


class ProviderManager:
    """Policy-enforcing, observable dispatch through the provider boundary."""

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        *,
        metrics: Any = None,
        audit: Any = None,
        policy: ProviderPolicy | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._registry = registry or ProviderRegistry()
        self._metrics = metrics
        self._audit = audit
        self._policy = policy or ProviderPolicy()
        self._timeout = timeout_seconds
        self._usage = ProviderUsage()
        self.last_provider: str | None = None
        #: Which provider the operator actually configured, as opposed to one
        #: merely registered. Reported separately so the UI never implies a
        #: language model exists because an adapter happens to be listed.
        self._configured_name: str | None = None

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    @property
    def usage(self) -> ProviderUsage:
        return self._usage

    def register(self, provider: Provider, profile: ProviderProfile | None = None) -> None:
        self._registry.register_instance(provider, profile)

    # -- selection -----------------------------------------------------------

    def select(self, *, required_capability: str | None = None) -> list[str]:
        """Policy-filtered candidate provider names (empty when none match)."""
        names, _status = self.select_detailed(required_capability=required_capability)
        return names

    def select_detailed(
        self,
        *,
        required_capability: str | None = None,
        check_health: bool = False,
    ) -> tuple[list[str], ProviderStatus]:
        """Select candidates and report *why* nothing was selected.

        The reason matters as much as the choice: a provider that is filtered
        out by policy, by budget, or by an unhealthy endpoint needs a different
        operator action, and collapsing them would make diagnosis guesswork.
        """
        policy = self._policy
        capability = required_capability or policy.required_capability
        instances = self._registry.instances()
        try:
            profile = self._registry.select(
                required_capability=capability,
                latency_budget_ms=policy.latency_budget_ms,
                cost_budget=policy.cost_budget,
                require_local=policy.require_local,
                require_privacy_approved=policy.require_privacy_approved,
                prefer=(self._registry.default,) if self._registry.default else (),
            )
        except Exception:  # noqa: BLE001 - no candidate matched the policy
            if not instances:
                return [], ProviderStatus.NOT_CONFIGURED
            self._usage.policy_rejections += 1
            budgets_bound = policy.cost_budget is not None or policy.latency_budget_ms is not None
            return [], (
                ProviderStatus.BUDGET_EXCEEDED if budgets_bound else ProviderStatus.UNAUTHORIZED
            )

        if check_health:
            try:
                if not profile_health(self._registry, profile.name):
                    self._fail("provider_unhealthy", profile.name)
                    return [], ProviderStatus.UNAVAILABLE
            except Exception:  # noqa: BLE001 - a broken probe is "unavailable"
                return [], ProviderStatus.UNAVAILABLE
        return [profile.name], ProviderStatus.OK

    def describe(self, *, check_health: bool = True) -> list[ProviderDescriptor]:
        """Truthful per-provider status for discovery and diagnostics.

        Reports REGISTERED / CONFIGURED / AVAILABLE / SUPPORTED separately and
        never includes credential material -- the key is not part of the shape.
        """
        configured = self._configured_name
        descriptors: list[ProviderDescriptor] = []
        for name in self._registry.names():
            profile = self._registry.get(name)
            available: bool | None = None
            if check_health and name in {p.name for p in self._registry.instances()}:
                available = profile_health(self._registry, name)
            states = [ProviderState.REGISTERED, ProviderState.SUPPORTED]
            if name == configured:
                states.append(ProviderState.CONFIGURED)
            if available:
                states.append(ProviderState.AVAILABLE)
            if name == self._registry.default:
                states.append(ProviderState.SELECTED)
            descriptors.append(
                ProviderDescriptor(
                    name=name,
                    kind=profile.kind,
                    model=self._model_of(name),
                    local=profile.local,
                    configured=name == configured,
                    registered=name in {p.name for p in self._registry.instances()},
                    available=available,
                    privacy_approved=profile.privacy_approved,
                    capabilities=profile.capabilities,
                    states=tuple(s.value for s in states),
                    timeout_seconds=self._timeout_of(name),
                    cost_per_call=profile.cost_per_call,
                    usage=dict(self._usage.by_provider),
                )
            )
        return descriptors

    def _model_of(self, name: str) -> str | None:
        try:
            return getattr(self._registry.get_instance(name), "model", None)
        except Exception:  # noqa: BLE001 - profile-only registration
            return None

    def _timeout_of(self, name: str) -> float:
        try:
            return float(getattr(self._registry.get_instance(name), "timeout_seconds", self._timeout))
        except Exception:  # noqa: BLE001 - profile-only registration
            return float(self._timeout)

    def provider_state(self) -> dict[str, Any]:
        """Compact provider status for ``/health`` (no credential material)."""
        descriptors = self.describe(check_health=False)
        return {
            "configured": self._configured_name,
            "count": len(descriptors),
            "providers": [d.to_dict() for d in descriptors],
            "usage": self._usage.snapshot(),
        }
# -- dispatch --------------------------------------------------------------

    def synthesize(
        self,
        *,
        question: str,
        conclusions: Any,
        verification: Any,
        cancellation: CancellationToken | None = None,
    ) -> str | None:
        """Ask the selected synthesis provider for a final safe answer.

        Returns ``None`` when no provider matches policy or when the call
        failed (a ``provider_failure`` signal is emitted and usage recorded);
        never raises — the caller falls back to deterministic synthesis.
        """
        if cancellation is not None and cancellation.cancelled:
            return None
        names, _status = self.select_detailed()
        if not names:
            return None
        safe_context = {
            "question": question,
            "conclusions": [c.to_dict() if hasattr(c, "to_dict") else str(c) for c in conclusions],
            "verification": verification,
        }
        return self._dispatch(
            names[0], question, context=safe_context, cancellation=cancellation
        )

    def generate(
        self,
        *,
        question: str,
        history: Sequence[dict[str, str]] = (),
        messages: Sequence[dict[str, str]] | None = None,
        authorized: bool = True,
        cancellation: CancellationToken | None = None,
    ) -> ProviderResult:
        """Generate an answer through an explicitly capable provider.

        Returns a :class:`ProviderResult` rather than ``str | None`` so the
        caller can tell "no provider is configured" from "the provider timed
        out" from "you are not allowed to use it" -- three different problems
        that must never be reported as one.

        ``messages`` is the Step 1A context already rendered by
        :mod:`aura.providers.handoff`; the manager never re-retrieves anything.
        """
        if not authorized:
            self._usage.policy_rejections += 1
            self._fail("provider_unauthorized", "caller")
            return ProviderResult(
                status=ProviderStatus.UNAUTHORIZED,
                error="this caller is not permitted to use a language model provider",
            )

        names, status = self.select_detailed(
            required_capability=ProviderCapability.GENERATION.value
        )
        if not names:
            return ProviderResult(status=status, error=_NO_PROVIDER_REASON[status])

        if cancellation is not None and cancellation.cancelled:
            return ProviderResult(
                status=ProviderStatus.CANCELLED,
                error="cancelled before dispatch",
                cancelled_stage="provider.dispatch",
            )

        safe_history = [
            {"role": message["role"], "content": message["content"][:4000]}
            for message in history[-20:]
            if message.get("role") in {"user", "assistant"} and isinstance(message.get("content"), str)
        ]
        return self._dispatch_result(
            names[0],
            question,
            mode="conversation",
            history=safe_history,
            messages=list(messages) if messages is not None else None,
            cancellation=cancellation,
        )

    def _dispatch(self, name: str, question: str, **kwargs: Any) -> str | None:
        """Backwards-compatible string dispatch (used by synthesis)."""
        cancellation = kwargs.pop("cancellation", None)
        result = self._dispatch_result(name, question, cancellation=cancellation, **kwargs)
        return result.text if result.ok else None

    def _dispatch_result(
        self,
        name: str,
        question: str,
        *,
        cancellation: CancellationToken | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        """One real provider call, returning a structured outcome."""
        self.last_provider = name
        provider = self._registry.get_instance(name)
        model = getattr(provider, "model", None)
        local = bool(getattr(getattr(provider, "profile", None), "local", False))

        if cancellation is not None and cancellation.cancelled:
            return ProviderResult(
                status=ProviderStatus.CANCELLED,
                provider=name,
                model=model,
                local=local,
                error="cancelled before dispatch",
                cancelled_stage="provider.dispatch",
            )

        try:
            started = time.monotonic()
            # Transport-capable adapters receive the token and abort in-flight
            # HTTP work; the embedded/provider fakes accept and ignore it.
            provider_kwargs = dict(kwargs)
            if cancellation is not None:
                provider_kwargs["cancellation"] = cancellation
            result = provider.reason(question, **provider_kwargs)
            latency_ms = (time.monotonic() - started) * 1000.0
        except CancelledError as exc:
            self._usage.failures += 1
            self._fail("provider_cancelled", name)
            return ProviderResult(
                status=ProviderStatus.CANCELLED,
                provider=name,
                model=model,
                local=local,
                error=str(exc),
                # The transport raises CancelledError only when it interrupted
                # a live HTTP request; other providers report the boundary.
                cancelled_stage="provider.http" if "mid-flight" in str(exc) else "provider",
            )
        except ProviderTimeoutError as exc:
            self._usage.timeouts += 1
            self._fail("provider_timeout", name)
            return self._failure_result(name, model, local, exc, ProviderStatus.TIMEOUT)
        except ProviderError as exc:
            self._usage.failures += 1
            status = _status_for(exc)
            self._fail(f"provider_{status.value}", name, str(exc))
            return self._failure_result(name, model, local, exc, status)
        except Exception as exc:  # noqa: BLE001 - boundary must never propagate
            self._usage.failures += 1
            self._fail("provider_unexpected", name, str(exc))
            return self._failure_result(name, model, local, exc, ProviderStatus.TRANSIENT_FAILURE)

        self._usage.calls += 1
        self._usage.total_latency_ms += latency_ms
        self._usage.note_provider(name)
        self._metric("provider_latency_ms", amount=latency_ms)
        self._metric("provider_call", amount=1)
        usage = ProviderCallUsage(calls=1, latency_ms=latency_ms)

        if result is None or str(result).strip() == "":
            return ProviderResult(
                status=ProviderStatus.MALFORMED_RESPONSE,
                provider=name,
                model=model,
                local=local,
                error="provider returned an empty response",
                usage=usage,
            )

        # Cooperative cancellation is honoured both here (before the response is
        # committed) and, for HTTP providers, in the transport itself: the
        # abort-aware client closes the connection while the request is in
        # flight, so cancellation is real interruption, not a post-hoc flag.
        if cancellation is not None and cancellation.cancelled:
            return ProviderResult(
                status=ProviderStatus.CANCELLED,
                provider=name,
                model=model,
                local=local,
                error="cancelled after the provider returned",
                usage=usage,
                cancelled_stage="provider.after_response",
            )

        return ProviderResult(
            status=ProviderStatus.OK,
            text=str(result),
            provider=name,
            model=model,
            local=local,
            usage=usage,
        )

    def _failure_result(
        self,
        name: str,
        model: str | None,
        local: bool,
        exc: Exception,
        status: ProviderStatus,
    ) -> ProviderResult:
        return ProviderResult(
            status=status,
            provider=name,
            model=model,
            local=local,
            error=str(exc),
            retryable=status in RETRYABLE_STATUSES,
        )

    # -- observability ---------------------------------------------------------

    def health(self) -> dict[str, bool]:
        return {p.name: bool(p.health()) for p in self._registry.instances()}

    def all_healthy(self) -> bool:
        if self._registry.instances():
            return all(p.health() for p in self._registry.instances())
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "providers": self._registry.names(),
            "default": self._registry.default,
            "usage": self._usage.snapshot(),
            "health": self.health(),
        }

    # -- internal -----------------------------------------------------------

    def _metric(self, name: str, amount: int | float = 1) -> None:
        increment = getattr(self._metrics, "increment", None)
        if callable(increment):
            with contextlib.suppress(Exception):
                increment(name, amount=amount)

    def _fail(self, kind: str, provider_name: str, detail: str = "") -> None:
        self._metric("provider_failure", amount=1)
        record = getattr(self._audit, "record", None)
        if callable(record):
            with contextlib.suppress(Exception):
                record(
                    action=f"provider.{kind}",
                    actor="system",
                    resource=provider_name,
                    decision="fallback",
                    reason=f"provider failure ({kind}); deterministic fallback used",
                    payload={"detail": detail} if detail else {},
                )


__all__ = ["ProviderManager", "build_provider_manager"]
