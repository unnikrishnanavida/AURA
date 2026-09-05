from __future__ import annotations
from dataclasses import dataclass,field
from ..models.goal import Goal
@dataclass(slots=True)
class DecompositionTree:
    root:Goal; children:dict[str,list[Goal]]=field(default_factory=dict)
    def add_child(self,parent:Goal,child:Goal):
        if child.goal_id==parent.goal_id: raise ValueError("cycle")
        if child.goal_id in {g.goal_id for g in self.children.get(parent.goal_id,())}: raise ValueError("duplicate child")
        self.children.setdefault(parent.goal_id,[]).append(child); child.parent_id=parent.goal_id
    def descendants(self,goal_id:str)->list[Goal]:
        result=[]; stack=list(self.children.get(goal_id,()))
        while stack:
            g=stack.pop(); result.append(g); stack.extend(self.children.get(g.goal_id,()))
        return result
    def leaves(self)->list[Goal]:
        all_nodes=[self.root,*self.descendants(self.root.goal_id)]; parents=set(self.children)
        return [g for g in all_nodes if g.goal_id not in parents]
