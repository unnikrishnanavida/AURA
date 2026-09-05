from dataclasses import dataclass


@dataclass(frozen=True)
class IPCMessage: channel:str; correlation_id:str; payload:dict
