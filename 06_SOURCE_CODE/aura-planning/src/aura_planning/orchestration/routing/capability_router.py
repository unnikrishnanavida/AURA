class CapabilityRouter:
    def __init__(self): self._providers={}
    def register(self,capability,provider):
        self._providers.setdefault(capability,[]).append(provider)
    def route(self,required):
        return [self._providers[c][0] for c in required if self._providers.get(c)]
