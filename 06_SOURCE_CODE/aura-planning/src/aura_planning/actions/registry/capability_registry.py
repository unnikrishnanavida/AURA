from collections import defaultdict
class CapabilityRegistry:
    def __init__(self): self._index=defaultdict(set)
    def register(self,action):
        for c in action.capabilities:
            if c.strip(): self._index[c].add(action.action_id)
    def actions_for(self,capability): return frozenset(self._index.get(capability,set()))
