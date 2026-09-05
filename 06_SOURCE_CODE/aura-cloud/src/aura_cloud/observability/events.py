from dataclasses import dataclass


@dataclass(frozen=True)
class CloudEvent: kind:str; correlation_id:str; payload:dict
