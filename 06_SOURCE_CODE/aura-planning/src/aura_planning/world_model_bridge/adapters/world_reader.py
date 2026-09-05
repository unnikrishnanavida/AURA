class WorldReader:
    def __init__(self, provider): self.provider=provider
    def read(self,query): return self.provider.read(query)
