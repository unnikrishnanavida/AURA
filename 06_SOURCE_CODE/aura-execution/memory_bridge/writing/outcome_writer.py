class OutcomeWriter:
    def __init__(self,store):self.store=store
    def write(self,outcome):self.store.append(outcome)
