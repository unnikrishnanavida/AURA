"""Remote provider adapter tests (transport-injected; no live endpoint)."""

from __future__ import annotations

from aura.providers.errors import (
    MalformedProviderResponse,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from aura.providers.remote import HttpChatProviderAdapter


class FakeTransport:
    """Records the request and returns a scripted (status, body)."""

    def __init__(self, status: int = 200, body: str = '{"choices": [{"message": {"content": "hello"}}]}') -> None:
        self.status = status
        self.body = body
        self.error: Exception | None = None
        self.requests: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def __call__(self, url: str, method: str, headers: dict[str, str], body: bytes | None, timeout: float) -> tuple[int, str]:
        if self.error is not None:
            raise self.error
        self.requests.append((url, method, headers, body))
        return self.status, self.body


def _adapter(*, flavor: str = "openai", **kw: object) -> HttpChatProviderAdapter:
    return HttpChatProviderAdapter(
        name="test",
        base_url="http://localhost:1",
        model="model-x",
        api_key="sk-test-1234567890",
        flavor=flavor,
        transport=FakeTransport(),
        **kw,  # type: ignore[arg-type]
    )


def test_openai_chat_request_shape() -> None:
    transport = FakeTransport()
    adapter = _adapter()
    adapter._transport = transport
    assert adapter.reason("question") == "hello"
    url, method, headers, body = transport.requests[0]
    assert url == "http://localhost:1/chat/completions"
    assert method == "POST"
    assert headers["Authorization"] == "Bearer sk-test-1234567890"
    import json

    payload = json.loads(body.decode())  # type: ignore[union-attr]
    assert payload["model"] == "model-x"
    assert payload["temperature"] == 0.0
    assert len(payload["messages"]) == 2


def test_provider_context_is_forwarded_as_evidence() -> None:
    transport = FakeTransport()
    adapter = _adapter()
    adapter._transport = transport
    adapter.reason("q", context={"question": "q", "conclusions": [{"statement": "A"}], "verification": {}})
    import json

    payload = json.loads(transport.requests[0][3].decode())  # type: ignore[union-attr]
    user_message = payload["messages"][1]["content"]
    assert "conclusions" in user_message


def test_http_error_maps_to_unavailable() -> None:
    adapter = _adapter()
    adapter._transport = FakeTransport(status=500, body="oops")
    try:
        adapter.reason("q")
        raise AssertionError("expected ProviderUnavailableError")
    except ProviderUnavailableError:
        pass


def test_malformed_json_maps() -> None:
    adapter = _adapter()
    adapter._transport = FakeTransport(body="not-json")
    try:
        adapter.reason("q")
        raise AssertionError("expected MalformedProviderResponse")
    except MalformedProviderResponse:
        pass


def test_missing_content_maps() -> None:
    adapter = _adapter()
    adapter._transport = FakeTransport(body='{"unexpected": true}')
    try:
        adapter.reason("q")
        raise AssertionError("expected MalformedProviderResponse")
    except MalformedProviderResponse:
        pass


def test_timeout_maps() -> None:
    adapter = _adapter()
    transport = FakeTransport()
    transport.error = TimeoutError("timed out")
    adapter._transport = transport
    try:
        adapter.reason("q")
        raise AssertionError("expected ProviderTimeoutError")
    except ProviderTimeoutError:
        pass


def test_ollama_flavor_uses_chat_endpoint_and_schema() -> None:
    transport = FakeTransport(body='{"message": {"content": "ollama says hi"}}')
    adapter = HttpChatProviderAdapter(
        name="ollama",
        base_url="http://localhost:11434",
        model="llama3",
        flavor="ollama",
        transport=transport,
    )
    assert adapter.reason("q") == "ollama says hi"
    url, _, _, body = transport.requests[0]
    assert url == "http://localhost:11434/api/chat"
    import json

    payload = json.loads(body.decode())  # type: ignore[union-attr]
    assert payload["stream"] is False


def test_health_ok_and_down() -> None:
    ok = _adapter()
    ok._transport = FakeTransport(status=200, body='{"data": []}')
    assert ok.health() is True

    down = _adapter()
    down._transport = FakeTransport(status=503, body="nope")
    assert down.health() is False