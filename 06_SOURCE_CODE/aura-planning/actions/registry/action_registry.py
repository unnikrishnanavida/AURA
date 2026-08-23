from threading import RLock
class ActionRegistry:
    def __init__(self): self._actions={}; self._lock=RLock()
    def register(self,action):
        action.validate()
        with self._lock:
            if action.action_id in self._actions: raise ValueError("duplicate action")
            self._actions[action.action_id]=action
    def resolve(self,i): return self._actions[i]
    def all(self): return tuple(self._actions.values())
