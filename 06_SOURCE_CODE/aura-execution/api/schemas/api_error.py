from dataclasses import dataclass
@dataclass
class ApiError:
    code:str
    message:str
