class TaskAllocator:
    def allocate(self,tasks,agents,cost):
        result={a:[] for a in agents}
        for task in sorted(tasks,key=cost,reverse=True):
            agent=min(agents,key=lambda a:sum(cost(t) for t in result[a]))
            result[agent].append(task)
        return result
