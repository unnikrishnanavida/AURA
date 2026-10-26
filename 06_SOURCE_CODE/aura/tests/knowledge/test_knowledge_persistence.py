"""Phase 2C: knowledge persistence (the outstanding 2A item) + retrieval quality.

Covers faithful Claim serialization, restart survival, owner isolation,
conflict/stale preservation, corrupt-row resilience, and paraphrase retrieval.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aura.foundation.errors import NotFoundError
from aura.knowledge.engine import KnowledgeBase, _claim_from_dict, _claim_to_dict
from aura.knowledge.models import Claim, Evidence, Source, VerificationStatus


def _claim(statement: str, *, evidence: bool = False) -> Claim:
    claim = Claim.create(statement=statement)
    if evidence:
        ev = Evidence(content="survey", source=Source(id="s1", reliability=0.8), quality=0.7)
        claim.with_evidence(ev, weight=0.3)
    return claim


def test_serialization_round_trip_is_faithful() -> None:
    c = _claim("Python is my preferred language.", evidence=True)
    d = _claim_to_dict(c)
    c2 = _claim_from_dict(d)
    assert str(c2.id) == str(c.id)
    assert c2.statement == c.statement
    assert c2.predicate == c.predicate
    assert c2.status == c.status
    assert c2.confidence == c.confidence
    assert c2.provenance.source == c.provenance.source
    assert len(c2.evidence) == len(c.evidence)
    assert c2.evidence[0].content == "survey"
    assert c2.evidence[0].source.reliability == 0.8


def test_knowledge_survives_restart(tmp_path) -> None:
    path = str(tmp_path / "k.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    kb1.add(_claim("Python is my preferred language."), owner="owner:a")
    kb1.add(_claim("SQL is for relational databases."), owner="owner:a")

    kb2 = KnowledgeBase(state_path=path)
    assert kb2.count() == 2, "knowledge did not survive restart"
    hits = kb2.retrieve(statement="which language do I prefer")
    assert any("Python" in c.statement for c, _ in hits)


def test_owner_isolation_survives_restart(tmp_path) -> None:
    path = str(tmp_path / "k2.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    claim = kb1.add(_claim("private-cookie-recipe"), owner="owner:a")

    kb2 = KnowledgeBase(state_path=path)
    assert kb2.retrieve(statement="cookie recipe", owner="owner:b") == []
    assert kb2.owner_of(claim.id) == "owner:a"
    private = kb2.retrieve(statement="cookie recipe", owner="owner:a")
    assert len(private) == 1


def test_conflicting_claims_survive_restart(tmp_path) -> None:
    path = str(tmp_path / "k3.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    kb1.add(Claim.create(statement="The sky is blue.", predicate=("sky",)), owner="owner:a")
    kb1.add(Claim.create(statement="The sky is not blue.", predicate=("sky",)), owner="owner:a")

    kb2 = KnowledgeBase(state_path=path)
    both = kb2.retrieve(statement="sky", owner="owner:a")
    assert len(both) == 2, "conflicts must not be silently dropped"
    assert kb2.contradictions(), "contradiction state was lost across restart"


def test_corrupt_row_does_not_block_startup(tmp_path) -> None:
    path = str(tmp_path / "k4.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    kb1.add(_claim("healthy claim"))
    from aura.foundation.persistent import SQLiteJsonStore

    store = SQLiteJsonStore(path, table="knowledge")
    store.put("v1", {"schema_version": 1, "claims": [{"id": "cl-broken"}], "scopes": {}})
    store.close()

    kb2 = KnowledgeBase(state_path=path)
    assert kb2.count() >= 0  # no crash; resilient startup


def test_paraphrase_knowledge_retrieval() -> None:
    kb = KnowledgeBase()
    kb.add(_claim("Python is my preferred programming language."))
    hits = kb.retrieve(statement="Which programming language do I like to code with?")
    assert any("Python" in c.statement for c, _ in hits)


def test_unrelated_knowledge_retrieval_is_controlled() -> None:
    kb = KnowledgeBase()
    kb.add(_claim("Python is my preferred programming language."))
    hits = kb.retrieve(statement="What is my favorite movie?")
    assert all("Python" not in c.statement for c, _ in hits) or not hits


# -- Phase 2C: direct-lookup owner isolation --------------------------------


def test_direct_lookup_enforces_owner(tmp_path) -> None:
    path = str(tmp_path / "k5.sqlite3")
    kb = KnowledgeBase(state_path=path)
    private = kb.add(_claim("the cookie recipe uses brown butter"), owner="owner:a")
    shared = kb.add(_claim("water boils at one hundred celsius"))

    # The owning scope sees its private claim; other scopes get NotFound
    # (never a silent leak or an existence oracle).
    assert str(kb.get(private.id, owner="owner:a").id) == str(private.id)
    with pytest.raises(NotFoundError):
        kb.get(private.id, owner="owner:b")

    # Claims with no owner scope stay shared: visible to every owner.
    assert str(kb.get(shared.id, owner="owner:b").id) == str(shared.id)
    # Without an owner filter (local/administrative read) the claim is visible.
    assert str(kb.get(private.id).id) == str(private.id)


def test_owner_isolation_on_get_survives_restart(tmp_path) -> None:
    path = str(tmp_path / "k6.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    claim = kb1.add(_claim("private-cookie-recipe"), owner="owner:a")

    kb2 = KnowledgeBase(state_path=path)
    with pytest.raises(NotFoundError):
        kb2.get(claim.id, owner="owner:b")
    assert str(kb2.get(claim.id, owner="owner:a").id) == str(claim.id)


# -- Phase 2C: corrupt persistence must never block startup ------------------


def test_store_error_during_hydrate_does_not_block_startup(tmp_path) -> None:
    path = str(tmp_path / "k7.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    kb1.add(_claim("healthy claim"))

    # A store that raises on read (e.g. disk/JSON failure) must degrade to an
    # empty knowledge base, never crash the process (historical NameError).
    class _ExplodingStore:
        def get(self, key: str):  # noqa: ANN001 - deliberate fault injection
            raise RuntimeError("simulated store read failure")

        def put(self, key: str, value: object) -> None:  # noqa: ANN001
            raise RuntimeError("simulated store write failure")

    kb1._store = _ExplodingStore()
    kb1._hydrate()  # must not raise
    # And persistence failures must not break subsequent writes either.
    kb1.add(_claim("claim added while store is broken"))
    assert kb1.count() >= 1


def test_non_dict_snapshot_is_ignored(tmp_path) -> None:
    from aura.foundation.persistent import SQLiteJsonStore

    path = str(tmp_path / "k8.sqlite3")
    store = SQLiteJsonStore(path, table="knowledge")
    store.put("v1", "corrupt-not-a-mapping")
    store.close()

    kb = KnowledgeBase(state_path=path)
    assert kb.count() == 0  # no crash; snapshot skipped entirely


def test_corrupt_rows_are_skipped_but_healthy_rows_survive(tmp_path) -> None:
    from aura.foundation.persistent import SQLiteJsonStore

    path = str(tmp_path / "k9.sqlite3")
    kb1 = KnowledgeBase(state_path=path)
    good = kb1.add(_claim("healthy claim"))

    # Corrupt one row while keeping another intact: only the bad row drops.
    store = SQLiteJsonStore(path, table="knowledge")
    raw = store.get("v1")
    assert isinstance(raw, dict) and isinstance(raw.get("claims"), list)
    raw["claims"].append({"id": "cl-broken", "statement": 123, "predicate": "not-a-list"})
    store.put("v1", raw)
    store.close()

    kb2 = KnowledgeBase(state_path=path)
    assert kb2.count() >= 1, "healthy rows must survive a corrupt neighbour"
    assert str(kb2.get(good.id).id) == str(good.id)


# -- Phase 2C: serialization edge cases --------------------------------------


def test_naive_created_at_is_normalized_on_rehydrate() -> None:
    claim = _claim("naive timestamp claim")
    claim.created_at = datetime(2024, 5, 1, 12, 0, 0)  # naive on purpose
    rebuilt = _claim_from_dict(_claim_to_dict(claim))
    assert rebuilt.created_at is not None
    assert rebuilt.created_at.tzinfo is not None  # no naive/aware arithmetic crash


def test_limit_must_be_positive() -> None:
    kb = KnowledgeBase()
    kb.add(_claim("anything at all"))
    with pytest.raises(ValueError):
        kb.retrieve(limit=0)


# -- Phase 2C: relevance-first ranking with trust tie-break ------------------


def test_equally_relevant_claims_rank_by_trust() -> None:
    kb = KnowledgeBase()
    now = datetime.now(UTC)

    stale = Claim.create(statement="database backups run at midnight", predicate=("backups",))
    stale.with_evidence(
        Evidence(content="rumour", source=Source(id="w", reliability=0.1), quality=0.1)
    )
    stale.created_at = now - timedelta(days=400)

    fresh = Claim.create(statement="database backups run at midnight", predicate=("backups",))
    fresh.with_evidence(
        Evidence(content="verified audit", source=Source(id="v", reliability=0.95), quality=0.95)
    )
    fresh.created_at = now - timedelta(hours=1)
    fresh.status = VerificationStatus.VERIFIED

    # Identical relevance (both exact-substring matches) -> trust decides.
    kb.add(stale)
    kb.add(fresh)
    hits = kb.retrieve(statement="database backups run at midnight")
    assert [c.statement for c, _ in hits].count("database backups run at midnight") == 2
    assert str(hits[0][0].id) == str(fresh.id), "fresher, verified, better-evidenced claim must rank first"


def test_non_overlapping_claims_are_excluded() -> None:
    kb = KnowledgeBase()
    kb.add(_claim("the migration completed without data loss"))
    hits = kb.retrieve(statement="cooking pasta with tomato sauce")
    assert hits == []