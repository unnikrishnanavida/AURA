class ScenarioRunner:
    def __init__(self,simulator): self.simulator=simulator
    def run(self,initial_state,scenarios):
        return tuple(self.simulator.run(initial_state.copy(),events) for events in scenarios)
