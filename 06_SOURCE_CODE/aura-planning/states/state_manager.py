from .models.planning_state import PlanningState
from .models.state_snapshot import StateSnapshot

class StateManager:
    def __init__(self, initial=None):
        self.current = initial if isinstance(initial, PlanningState) else PlanningState(dict(initial or {}))
        self.history = [StateSnapshot.capture(self.current)]

    def transition(self, action):
        outcome = action.apply(self.current)
        if not outcome.success:
            return outcome
        self.current = outcome.state
        self.history.append(StateSnapshot.capture(self.current))
        return outcome

    def snapshot(self): return StateSnapshot.capture(self.current)
    def restore(self, snapshot):
        self.current = snapshot.state
        self.history.append(snapshot)
