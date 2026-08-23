import pytest
@pytest.fixture
def simple_state():
    try:
        from aura_planning.states.models.planning_state import PlanningState
        return PlanningState({"ready":True})
    except ImportError:
        return {"ready":True}
