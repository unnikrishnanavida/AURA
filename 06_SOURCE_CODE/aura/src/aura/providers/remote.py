"""Remote chat-completion provider adapters.

Real HTTP client code for OpenAI-compatible endpoints and Ollama. Design:

- **Credential-safe** — ``api_key`` is stored on the adapter and used only to
  build the Authorization header; it is never logged or echoed in errors.
- **Transport-injectable** — tests inject a fake transport so the full request
  path (URL, headers, body, parsing, error mapping) is verified without a live
  endpoint.
- **Honest status** — these adapters are contract-implemented and
  unit-tested; *live* verification requires operator-supplied base URLs /
  API keys and is NOT claimed here (no credentials are available).
"""

from __future__ import annotations

import json
from typing import Any, cast

from aura.providers.base import Provider, ProviderProfile
from aura.providers.errors import (
    MalformedProviderResponse,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

_DEFAULT_SYSTEM = (
    "You are AURA, a careful reasoning assistant. "
    "Synthesize a concise final answer from the provided evidence only. "
    "If the evidence is insufficient say exactly: I do not know"
)


class HttpChatProviderAdapter(Provider):
    """OpenAI-compatible / Ollama chat-completion provider."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: float = 15.0,
        flavor: str = "openai",
        privacy_approved: bool = False,
        transport: Any = None,
    ) -> None:
        self.name = name
        self.timeout_seconds = timeout_seconds
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._flavor = flavor
        self._transport = transport
        self.profile = ProviderProfile(
            name=name,
            kind="reasoning",
            capabilities=("reasoning.synthesis", "reasoning.generation"),
            latency_ms=400.0,
            cost_per_call=0.01,
            reliability=0.95,
            local=(flavor == "ollama"),
            privacy_approved=privacy_approved,
        )

    # -- contract ------------------------------------------------------------

    def health(self) -> bool:
        """Reachability probe: HTTP 200 from the models/tags endpoint."""
        try:
            status, _ = self._call(self._health_request())
            return status == 200
        except Exception:  # noqa: BLE001 - health must not raise
            return False

    def reason(self, question: str, **kwargs: Any) -> str:
        context = kwargs.get("context")
        prompt = f"{question}\n\nEvidence:\n{json.dumps(context, sort_keys=True, default=str)}" if context else question
        return self._chat(self._chat_request(prompt))

    # -- request construction ------------------------------------------------

    def _health_request(self) -> dict[str, Any]:
        return {
            "url": f"{self._base_url}/models" if self._flavor == "openai" else f"{self._base_url}/api/tags",
            "method": "GET",
            "headers": ({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            "body": None,
        }

    def _chat_request(self, prompt: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": _DEFAULT_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        if self._flavor == "ollama":
            return {
                "url": f"{self._base_url}/api/chat",
                "method": "POST",
                "headers": {},
                "body": {"model": self._model, "messages": messages, "stream": False, "temperature": 0.0},
            }
        return {
            "url": f"{self._base_url}/chat/completions",
            "method": "POST",
            "headers": ({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            "body": {"model": self._model, "messages": messages, "temperature": 0.0},
        }

    # -- transport -------------------------------------------------------------

    def _call(self, request: dict[str, Any]) -> tuple[int, str]:
        body = json.dumps(request["body"]).encode() if request["body"] is not None else None
        headers = dict(request["headers"])
        headers.setdefault("Content-Type", "application/json")

        if self._transport is not None:
            try:
                return cast(tuple[int, str], self._transport(request["url"], request["method"], headers, body, self.timeout_seconds))
            except TimeoutError:
                raise ProviderTimeoutError(f"provider timed out: {self.name}") from None
            except OSError as exc:
                raise ProviderUnavailableError(f"provider unreachable: {self.name}: {exc}") from exc

        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            request["url"], data=body, headers=headers, method=request["method"]
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return int(resp.getcode()), resp.read().decode("utf-8", errors="replace")
        except TimeoutError:
            raise ProviderTimeoutError(f"provider timed out: {self.name}") from None
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError(f"provider unreachable: {self.name}: {exc}") from exc

    def _chat(self, request: dict[str, Any]) -> str:
        status, raw = self._call(request)
        if status != 200:
            raise ProviderUnavailableError(f"provider HTTP {status}: {self.name}")
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise MalformedProviderResponse(f"provider returned non-JSON: {self.name}") from exc
        try:
            if self._flavor == "ollama":
                return str(data["message"]["content"])
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise MalformedProviderResponse(f"provider response missing content: {self.name}") from exc


__all__ = ["HttpChatProviderAdapter"]