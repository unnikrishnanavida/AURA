from dataclasses import dataclass,field
from enum import Enum
class Status(str,Enum): PENDING='pending'; RUNNING='running'; SUCCEEDED='succeeded'; FAILED='failed'; CANCELLED='cancelled'
@dataclass(frozen=True)
class Action: action_id:str; capability:str; parameters:dict=field(default_factory=dict); reversible:bool=False
@dataclass
class ExecutionRecord: execution_id:str; status:Status; actions:list; events:list=field(default_factory=list)
