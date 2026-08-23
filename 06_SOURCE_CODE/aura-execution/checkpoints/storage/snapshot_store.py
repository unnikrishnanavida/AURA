class SnapshotStore:
    def __init__(self):self.snapshots={}
    def save(self,id,state):self.snapshots[id]=dict(state)
    def load(self,id):return dict(self.snapshots[id])
