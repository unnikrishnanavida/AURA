class StateValidator:
    def require(self,state,requirements):
        return all(state.get(k)==v for k,v in requirements.items())
