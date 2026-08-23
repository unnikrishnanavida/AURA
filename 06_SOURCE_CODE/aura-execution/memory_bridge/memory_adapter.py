class MemoryAdapter:
    def __init__(self,retriever,writer):self.retriever=retriever;self.writer=writer
    def recall(self,action_id):return self.retriever.similar(action_id)
    def remember(self,item):self.writer.write(item)
