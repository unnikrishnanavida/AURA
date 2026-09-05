from aura_research.analysis.calibration import calibrate
def test_contradiction_reduces_confidence(): assert calibrate(1,1)<calibrate(1,0)
