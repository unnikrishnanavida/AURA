from dataclasses import dataclass
from enum import Enum


class Permission(str,Enum): READ='read'; WRITE='write'; EXECUTE='execute'
@dataclass(frozen=True)
class DesktopAction: action_id:str; capability:str; permission:Permission; payload:dict
