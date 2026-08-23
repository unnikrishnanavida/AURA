class ExecutionReconstructor:
    def reconstruct(self,events):
        return {"execution_id":events[0].execution_id if events else None,"events":[e.event for e in events]}
