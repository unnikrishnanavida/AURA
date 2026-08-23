from dataclasses import dataclass
@dataclass
class ApiRequest:
    action_id:str
    inputs:dict
