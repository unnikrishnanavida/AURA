from aura_research.engine import ResearchEngine
from aura_research.core.question import ResearchQuestion
def test_empty_evidence_honesty():
    r=ResearchEngine().research(ResearchQuestion("unknown"))
    assert r.confidence==0 and "do not know" in r.answer.lower()
