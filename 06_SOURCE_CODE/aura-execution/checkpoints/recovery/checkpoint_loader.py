class CheckpointLoader:
    def __init__(self,store):self.store=store
    def load(self,id):return self.store.load(id)
