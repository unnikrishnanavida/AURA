def test_safety_policy():
    from aura_planning.safety.policies.safety_policy import SafetyPolicy
    policy=SafetyPolicy("deny", (lambda x: "blocked" if x=="bad" else None,))
    assert policy.evaluate("bad")==("blocked",)
    assert policy.evaluate("good")==()
