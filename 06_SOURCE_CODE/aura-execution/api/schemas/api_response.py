from dataclasses import dataclass
@dataclass
class ApiResponse:
    status:str
    data:object=None
