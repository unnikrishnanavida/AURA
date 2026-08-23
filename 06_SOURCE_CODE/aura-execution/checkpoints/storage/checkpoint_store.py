class CheckpointStore:
    def __init__(self):self.data={}
    def save(self,checkpoint):self.data[checkpoint.id]=checkpoint
    def load(self,id):return self.data[id]
