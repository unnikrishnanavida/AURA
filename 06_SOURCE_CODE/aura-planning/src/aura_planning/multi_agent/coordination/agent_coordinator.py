class AgentCoordinator:
    def __init__(self,policy): self.policy=policy
    def coordinate(self,agents,tasks,allocator):
        self.policy.validate()
        return allocator.allocate(tasks,agents,lambda x:getattr(x,"cost",1))
