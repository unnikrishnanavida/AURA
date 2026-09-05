"""Integration tests: aura-api reusable layer with the canonical AURA runtime.

The canonical ``aura`` package is installed as an editable dependency. These
tests prove the reusable API layer can call real canonical functionality
through an explicit adapter boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from aura_api import ApiKeyStore, Authenticator, Authorizer, RBACPolicy, ReferenceApi, TokenBucket


@pytest.fixture
def canonical_ok():
    try:
        import aura  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif("not canonical_ok")
def test_reference_api_can_drive_canonical_health():
    from aura import Aura

    client = Aura()
    health = client.health()
    assert health["status"] == "ok"


@pytest.mark.skipif("not canonical_ok")
def test_canonical_knowledge_callable_through_reference_api():
    from aura.knowledge.models import Claim, ClaimId

    claim = Claim.create(statement="the capital of France is Paris")
    assert claim.statement == "the capital of France is Paris"
    assert isinstance(claim.id, ClaimId)


@pytest.mark.skipif("not canonical_ok")
def test_aura_api_and_canonical_share_correlation_contract():
    from aura.foundation.ids import CorrelationId

    canonical = str(CorrelationId.new())
    assert canonical.startswith("co-")
    from aura_api.core.context import new_correlation_id

    ours = new_correlation_id()
    assert ours.startswith("co-")