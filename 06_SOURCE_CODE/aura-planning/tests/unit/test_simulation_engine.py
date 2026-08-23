def test_simulation():
    from aura_planning.simulation.models.simulation_state import SimulationState
    from aura_planning.simulation.models.simulation_event import SimulationEvent
    from aura_planning.simulation.core.simulator import Simulator
    def set_ready(state,event): state.values["ready"]=event.payload
    state,history=Simulator({"ready":set_ready}).run(SimulationState(),[SimulationEvent(1,"ready",True)])
    assert state.values["ready"] is True and len(history)==1
