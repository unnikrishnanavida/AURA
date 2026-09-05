from aura_research.uncertainty.abstention import honest_answer
def test_abstain(): assert "do not know" in honest_answer(.1).lower()
