def test_identical_action_sequences_have_identical_state():
    from aura_planning.states.models.planning_state import PlanningState
    from aura_planning.actions.models.action import Action
    from aura_planning.actions.models.action_effect import ActionEffect
    action=Action("x","x",effects=(ActionEffect("value",1),))
    first=action.apply(PlanningState()).state
    second=action.apply(PlanningState()).state
    assert first.values==second.values
