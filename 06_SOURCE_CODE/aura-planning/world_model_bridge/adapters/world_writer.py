class WorldWriter:
    def __init__(self, provider): self.provider=provider
    def write(self,observation): return self.provider.write(observation)
