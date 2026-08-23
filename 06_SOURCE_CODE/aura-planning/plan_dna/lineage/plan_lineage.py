class PlanLineage:
    def __init__(self): self.parent={}; self.changes={}
    def derive(self,parent_id,child_id,changes=()):
        if child_id in self.parent: raise ValueError(f"plan already has lineage: {child_id}")
        self.parent[child_id]=parent_id; self.changes[child_id]=tuple(changes)
    def ancestors(self,plan_id):
        result=[]; current=plan_id
        while current in self.parent:
            current=self.parent[current]; result.append(current)
        return tuple(result)
