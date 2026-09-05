"""Shared fixtures for AURA platform tests."""

from __future__ import annotations

from datetime import UTC

import pytest

from aura.brain.engine import BrainEngine
from aura.foundation.clock import FrozenClock
from aura.sdk.client import Aura


@pytest.fixture
def clock() -> FrozenClock:
    from datetime import datetime

    return FrozenClock(datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC))


@pytest.fixture
def brain(clock: FrozenClock) -> BrainEngine:
    return BrainEngine.create(clock=clock, seed=42)


@pytest.fixture
def aura(clock: FrozenClock) -> Aura:
    return Aura(clock=clock, seed=42)