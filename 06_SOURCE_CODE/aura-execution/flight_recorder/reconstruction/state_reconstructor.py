class StateReconstructor:
    def reconstruct(self,initial,events):
        state=dict(initial)
        for e in events:
            state.update(e.data.get("state",{}))
        return state
