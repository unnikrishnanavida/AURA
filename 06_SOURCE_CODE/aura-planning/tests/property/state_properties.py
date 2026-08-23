def test_state_update_is_persistent():
    from aura_planning.states.models.planning_state import PlanningState
    original=PlanningState({"x":1})
    updated=original.with_value("x",2)
    assert original.get("x")==1
    assert updated.get("x")==2
