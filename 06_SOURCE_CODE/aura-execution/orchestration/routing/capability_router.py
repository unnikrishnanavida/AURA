class CapabilityRouter:
    def __init__(self,engine):self.engine=engine
    def route(self,action):return self.engine.check(action.capability,action.name)
