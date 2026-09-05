from dataclasses import dataclass
from enum import Enum


class Connectivity(str,Enum): OFFLINE='offline'; LIMITED='limited'; ONLINE='online'
@dataclass(frozen=True)
class SyncItem: item_id:str; version:int; payload:dict
