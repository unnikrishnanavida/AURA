from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class Metric:
    name:str; value:float; timestamp:float; tags:dict
