from ...kernel.identity.fingerprint import fingerprint
class DuplicateStatePruner:
    def __init__(self): self.seen=set()
    def accept(self,state):
        key=fingerprint(getattr(state,"values",state))
        if key in self.seen:return False
        self.seen.add(key);return True
    def reset(self): self.seen.clear()
