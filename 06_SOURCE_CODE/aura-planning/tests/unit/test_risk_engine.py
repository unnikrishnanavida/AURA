def test_risk_exposure():
    from aura_planning.risk.models.risk import Risk
    risk=Risk("failure",.5,.8)
    assert risk.exposure==.4
