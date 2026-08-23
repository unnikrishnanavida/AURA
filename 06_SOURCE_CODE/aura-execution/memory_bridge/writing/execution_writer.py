class ExecutionWriter:
    def __init__(self,store):self.store=store
    def write(self,execution):self.store.append(execution)
