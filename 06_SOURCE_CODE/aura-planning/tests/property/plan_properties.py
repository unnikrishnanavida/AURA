def test_action_application_changes_expected_state():
    from aura_planning.states.models.planning_state import PlanningState
    from aura_planning.actions.models.action import Action
    from aura_planning.actions.models.action_effect import ActionEffect
    state=PlanningState({"ready":False})
    action=Action("enable","Enable",effects=(ActionEffect("ready",True),))
    result=action.apply(state)
    assert result.success and result.state.get("ready") is True
