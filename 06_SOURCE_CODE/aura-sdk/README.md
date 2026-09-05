# aura-sdk

Developer SDK for the canonical AURA integrated reasoning platform.

> **Architectural rule:** this package is a *client* of the canonical runtime at
> `06_SOURCE_CODE/aura`. It never re-implements reasoning, memory, learning,
> planning, or security. All behavior is delegated to the canonical runtime (in
> local mode) or to the canonical HTTP API (in remote mode).

## Modes

| Mode    | Transport       | Description                                              |
| ------- | --------------- | -------------------------------------------------------- |
| `LOCAL` | `LocalTransport`| In-process canonical `aura.Aura`, deterministic, no network |
| `HTTP`  | `HttpTransport` | Remote `aura-api` server over HTTP with bearer auth      |

## Quick start (local mode)

```python
from aura_sdk import AuraSDK, SdkConfig
from aura_sdk.config import TransportMode

client = AuraSDK(config=SdkConfig(mode=TransportMode.LOCAL))

client.remember("deployment-state", {"phase": "canary"}, kind="episodic")
print(client.recall("deployment"))
print(client.reason("is the canary healthy?", facts={"healthy": 0.9}))
print(client.metrics())
```

## Quick start (HTTP mode)

```python
from aura_sdk import AuraSDK, SdkConfig
from aura_sdk.config import TransportMode

client = AuraSDK(
    config=SdkConfig(
        mode=TransportMode.HTTP,
        endpoint="http://127.0.0.1:8765",
        api_key="an-api-key-at-least-8-chars",
        timeout_seconds=15,
    )
)
client.health()
```

## Architecture

`client` (facade) → `middleware` (ids + redaction) → `transport`
(local in-process or HTTP) → canonical `aura` runtime / `aura-api` server.
Typed errors live in `errors.py`; retries/backoff in `retry.py`; auth in
`authentication.py`; events in `events.py`; sessions in `sessions.py`.

## Security

- The API key is never rendered; `describe()` masks the tail.
- `SdkConfig.to_public_dict()` never includes secret material.
- The same `api_key` cannot be used in local mode (no remote boundary).
- Retries only retry *transient* failures (timeout/transport). 4xx API errors
  fail immediately.

## Testing

```bash
python -m pytest tests/ -q
```

Local-mode tests run against the in-process canonical runtime; HTTP tests
start a real `AuraApiServer` on a loopback port and exercise bearer auth,
timeouts, and error mapping.