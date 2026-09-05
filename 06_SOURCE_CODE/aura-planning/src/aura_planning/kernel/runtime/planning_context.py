from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterator

@dataclass(slots=True)
class PlanningContext:
    request_id: str
    values: dict[str,Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    parent_id: str|None = None

    def get(self,key:str,default:Any=None)->Any: return self.values.get(key,default)
    def require(self,key:str)->Any:
        if key not in self.values: raise KeyError(f"missing context key: {key}")
        return self.values[key]
    def with_value(self,key:str,value:Any)->"PlanningContext":
        values=dict(self.values); values[key]=value
        return PlanningContext(self.request_id,values,set(self.tags),self.parent_id)
    def with_tag(self,tag:str)->"PlanningContext":
        if not tag.strip(): raise ValueError("tag cannot be empty")
        return PlanningContext(self.request_id,dict(self.values),self.tags|{tag.strip()},self.parent_id)
    def items(self)->Iterator[tuple[str,Any]]: return iter(self.values.items())
