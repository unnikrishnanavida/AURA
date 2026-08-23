class DecompositionPlanner:
    def __init__(self,rules): self.rules=dict(rules)
    def decompose(self,task):
        if task.primitive: return (task,)
        rule=self.rules.get(task.task_id)
        if rule is None: raise KeyError(f"no decomposition rule for {task.task_id}")
        result=[]
        for child in rule(task):
            result.extend(self.decompose(child))
        return tuple(result)
