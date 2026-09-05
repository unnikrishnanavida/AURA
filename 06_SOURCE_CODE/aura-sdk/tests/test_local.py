"""Local-mode SDK tests: initialization, reasoning, memory, knowledge, research, sessions, events."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aura_sdk import (  # noqa: E402
    AuraSDK,
    SdkConfig,
    SdkEvent,
    SdkValidationError,
)
from aura_sdk.config import TransportMode  # noqa: E402


@pytest.fixture
def client() -> AuraSDK:
    return AuraSDK(config=SdkConfig(mode=TransportMode.LOCAL), seed=1)


def test_initialization_and_health(client: AuraSDK) -> None:
    assert client.start().startswith("AURA SDK")
    assert client.health()["status"] == "ok"


def test_reason_and_recall_flow(client: AuraSDK) -> None:
    memory_id = client.remember("alpha", {"value": 1})
    assert memory_id
    entries = client.recall("alpha")
    assert entries and entries[0]["key"] == "alpha"


def test_observe_and_research(client: AuraSDK) -> None:
    claim_id = client.observe("deployment requires approval", predicate=("safety",))
    assert claim_id
    output = client.research("Is deployment approved?", claims=("deployment requires approval",))
    assert "findings" in output


def test_events_are_published(client: AuraSDK) -> None:
    seen: list[str] = []

    def on_event(event: SdkEvent) -> None:
        seen.append(event.event_type)

    client.events.subscribe(on_event)
    client.health()
    assert "sdk.request" in seen
    assert "sdk.response" in seen


def test_invalid_operation_raises(client: AuraSDK) -> None:
    with pytest.raises(SdkValidationError):
        client.execute("does_not_exist")


def test_session_management() -> None:
    client = AuraSDK()
    session = client.session()
    assert session.id
    assert session.identity == "sdk-user"