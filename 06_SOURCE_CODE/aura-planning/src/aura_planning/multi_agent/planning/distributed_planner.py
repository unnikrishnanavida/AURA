class DistributedPlanner:
    def __init__(self,agents): self.agents=tuple(agents)
    def plan(self,tasks):
        results=[]
        for agent,task in zip(self.agents,tasks):
            results.append(agent.plan(task))
        return tuple(results)
