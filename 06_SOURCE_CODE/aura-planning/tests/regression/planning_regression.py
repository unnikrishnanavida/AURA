def test_forward_planning_reaches_goal():
    from aura_planning.states.models.planning_state import PlanningState
    from aura_planning.goals.models.goal_state import GoalState
    from aura_planning.actions.models.action import Action
    from aura_planning.actions.models.action_effect import ActionEffect
    from aura_planning.planners.classical.forward_planner import ForwardPlanner
    action=Action("finish","Finish",effects=(ActionEffect("done",True),))
    result=ForwardPlanner((action,)).plan(PlanningState({"done":False}),GoalState({"done":True}))
    assert result.success
