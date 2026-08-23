class BaselineManager:
    def __init__(self): self._baselines={}
    def set(self,name,metrics): self._baselines[name]=dict(metrics)
    def get(self,name): return dict(self._baselines[name])
    def names(self): return tuple(self._baselines)
