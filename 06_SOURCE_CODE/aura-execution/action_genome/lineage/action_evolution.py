class ActionEvolution:
    def __init__(self):self.versions={}
    def add(self,action_id,version):self.versions.setdefault(action_id,[]).append(version)
    def history(self,action_id):return tuple(self.versions.get(action_id,()))
