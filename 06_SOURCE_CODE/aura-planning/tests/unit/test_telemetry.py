def test_histogram():
    from aura_planning.telemetry.metrics.histogram import Histogram
    h=Histogram(); h.observe(1); h.observe(3)
    assert h.summary()["mean"]==2
