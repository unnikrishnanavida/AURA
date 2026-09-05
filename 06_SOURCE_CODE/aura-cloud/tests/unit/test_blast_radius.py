from aura_cloud.planning.blast_radius import BlastRadius,risk_score
def test_risk(): assert risk_score(BlastRadius(0,10))>risk_score(BlastRadius(10,0))
