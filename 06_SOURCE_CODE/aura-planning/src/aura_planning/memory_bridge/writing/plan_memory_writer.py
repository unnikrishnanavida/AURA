class PlanMemoryWriter:
    def __init__(self,store): self.store=store
    def write(self,memory): self.store.put(memory)
