import uuid
from .models.checkpoint import Checkpoint
class CheckpointEngine:
    def __init__(self,store):self.store=store
    def create(self,eid,state):
        c=Checkpoint(str(uuid.uuid4()),eid,dict(state));self.store.save(c);return c
