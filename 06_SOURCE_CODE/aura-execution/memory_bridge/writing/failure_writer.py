class FailureWriter:
    def __init__(self,store):self.store=store
    def write(self,failure):self.store.append(failure)
