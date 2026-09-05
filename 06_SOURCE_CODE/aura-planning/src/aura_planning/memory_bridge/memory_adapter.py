class MemoryAdapter:
    def __init__(self,retriever,writer): self.retriever,self.writer=retriever,writer
    def retrieve(self,goal_key,limit=5): return self.retriever.retrieve(goal_key,limit)
    def remember(self,memory): self.writer.write(memory)
