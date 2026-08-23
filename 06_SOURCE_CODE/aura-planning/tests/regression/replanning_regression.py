def test_replanning_detects_state_deviation():
    from aura_planning.replanning.analysis.deviation_analyzer import DeviationAnalyzer
    result=DeviationAnalyzer().analyze({"x":1},{"x":2})
    assert result["x"]==(1,2)
