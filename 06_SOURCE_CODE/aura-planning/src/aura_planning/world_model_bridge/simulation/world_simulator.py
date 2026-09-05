class WorldSimulator:
    def __init__(self,simulation_engine): self.engine=simulation_engine
    def predict(self,plan,state):
        return self.engine.evaluate((plan,),state)[0]
