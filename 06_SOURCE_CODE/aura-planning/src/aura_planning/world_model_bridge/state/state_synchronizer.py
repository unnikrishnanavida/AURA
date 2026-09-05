class StateSynchronizer:
    def __init__(self, reader, adapter): self.reader,self.adapter=reader,adapter
    def sync(self, queries): return self.adapter.to_planning_state([self.reader.read(q) for q in queries])
