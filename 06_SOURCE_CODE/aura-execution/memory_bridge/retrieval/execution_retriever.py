class ExecutionRetriever:
    def __init__(self,store):self.store=store
    def similar(self,action_id):return [x for x in self.store if x.action_id==action_id]
