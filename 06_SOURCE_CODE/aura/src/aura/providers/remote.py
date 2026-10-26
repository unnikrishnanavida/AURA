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
import select
import time
from http.client import HTTPConnection, HTTPSConnection
from typing import Any, cast
from urllib.parse import urlparse

from aura.foundation.errors import CancelledError
from aura.providers.base import Provider, ProviderProfile
from aura.providers.errors import (
    MalformedProviderResponse,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

#: How often the abort-aware HTTP client re-checks the cancellation token while
#: waiting for a provider response. Cancellation latency is bounded by this
#: interval, so an interrupted request is observed within ~50ms.
_ABORT_POLL_SECONDS = 0.05

_DEFAULT_SYSTEM = (
    "You are AURA, a careful reasoning assistant. "
    "Synthesize a concise final answer from the provided evidence only. "
    "If the evidence is insufficient say exactly: I do not know"
)
_CONVERSATION_SYSTEM = (
    "You are AURA, a helpful and careful AI assistant. Answer the latest user message clearly and naturally, "
    "using prior conversation only as context. Be honest when uncertain. Do not claim to have used tools, "
    "searched data, or completed actions unless the request includes those results. Do not reveal hidden reasoning."
)


class _call_interrupted(Exception):
    """Internal control flow: the token was cancelled during a provider call."""


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
        self.model = model
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
        # The manager hands the caller's token through so the live HTTP request
        # can genuinely be interrupted mid-flight instead of only checked after.
        cancellation = kwargs.get("cancellation")
        # A caller that already assembled the bounded, sectioned handoff (the
        # Step 1A context contract) hands us the exact messages to send. Those
        # must be used verbatim: rebuilding the prompt here would discard the
        # authorized-context sections and quietly send something else.
        prebuilt = kwargs.get("messages")
        if isinstance(prebuilt, list) and prebuilt:
            return self._chat(self._messages_request(prebuilt), cancellation=cancellation)
        if kwargs.get("mode") == "conversation":
            history = self._conversation_history(kwargs.get("history", ()))
            return self._chat(
                self._chat_request(
                    question,
                    system_prompt=_CONVERSATION_SYSTEM,
                    history=history,
                ),
                cancellation=cancellation,
            )
        context = kwargs.get("context")
        prompt = f"{question}\n\nEvidence:\n{json.dumps(context, sort_keys=True, default=str)}" if context else question
        return self._chat(self._chat_request(prompt), cancellation=cancellation)

    @staticmethod
    def _conversation_history(history: Any) -> list[dict[str, str]]:
        if not isinstance(history, (list, tuple)):
            return []
        messages = []
        for message in history[-20:]:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content[:4000]})
        return messages

    # -- request construction ------------------------------------------------

    def _health_request(self) -> dict[str, Any]:
        return {
            "url": f"{self._base_url}/models" if self._flavor == "openai" else f"{self._base_url}/api/tags",
            "method": "GET",
            "headers": ({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            "body": None,
        }

    def _messages_request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Build a chat request from a caller-supplied message list verbatim."""
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

    def _chat_request(
        self,
        prompt: str,
        *,
        system_prompt: str = _DEFAULT_SYSTEM,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": prompt})
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

    def _call(self, request: dict[str, Any], *, cancellation: Any = None) -> tuple[int, str]:
        """Perform one provider HTTP call.

        The injectable transport (used by the unit suite) stays the fastest,
        most deterministic path. The real transport is the abort-aware stdlib
        client in :meth:`_call_http`: it polls the cancellation token while the
        request is in flight and closes the connection on cancellation, so an
        interrupted provider call is observed in real time rather than merely
        after the response arrives.
        """
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

        return self._call_http(request, body, headers, cancellation=cancellation)

    def _call_http(
        self,
        request: dict[str, Any],
        body: bytes | None,
        headers: dict[str, str],
        *,
        cancellation: Any = None,
    ) -> tuple[int, str]:
        """Abort-aware provider HTTP client (stdlib-only).

        The socket is polled every ``_ABORT_POLL_SECONDS``; when the token is
        cancelled the connection is closed and :class:`CancelledError` propagates
        so the manager reports ``provider.http`` as the cancelled stage. The
        absolute deadline still enforces the configured timeout.
        """
        parsed = urlparse(request["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ProviderUnavailableError(f"unsupported provider URL: {request['url']!r}")
        secure = parsed.scheme == "https"
        port = parsed.port or (443 if secure else 80)
        conn: HTTPConnection | HTTPSConnection = (HTTPSConnection if secure else HTTPConnection)(
            parsed.hostname, port, timeout=self.timeout_seconds
        )
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        deadline = time.monotonic() + max(self.timeout_seconds, _ABORT_POLL_SECONDS)

        def _interrupted() -> None:
            if cancellation is not None and cancellation.cancelled:
                conn.close()
                raise _call_interrupted("provider request interrupted mid-flight") from None

        try:
            conn.request(request["method"], path, body=body, headers=headers)
            sock = conn.sock
            if sock is None:
                raise ProviderUnavailableError(f"provider connection unavailable: {self.name}")
            sock.settimeout(_ABORT_POLL_SECONDS)
            # Wait for response headers, polling the token the whole time.
            while True:
                _interrupted()
                readable, _, _ = select.select([sock], [], [], _ABORT_POLL_SECONDS)
                if readable:
                    break
                if time.monotonic() >= deadline:
                    raise ProviderTimeoutError(f"provider timed out: {self.name}")
            response = conn.getresponse()
            # Read the body; a stalled provider still honours the deadline and
            # a cancelled caller still aborts the connection immediately.
            chunks: list[bytes] = []
            while True:
                _interrupted()
                try:
                    chunk = response.read(65536)
                except TimeoutError:
                    if time.monotonic() >= deadline:
                        raise ProviderTimeoutError(f"provider timed out: {self.name}") from None
                    continue
                if not chunk:
                    break
                chunks.append(chunk)
            status = int(response.status)
            return status, b"".join(chunks).decode("utf-8", errors="replace")
        except _call_interrupted as exc:
            raise CancelledError(str(exc)) from None
        except TimeoutError as exc:
            raise ProviderTimeoutError(f"provider timed out: {self.name}") from exc
        except OSError as exc:
            raise ProviderUnavailableError(f"provider unreachable: {self.name}: {exc}") from exc
        finally:
            conn.close()

    def _chat(self, request: dict[str, Any], *, cancellation: Any = None) -> str:
        status, raw = self._call(request, cancellation=cancellation)
        if status != 200:
            raise ProviderUnavailableError(
                f"provider HTTP {status}: {self.name}", http_status=status
            )
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