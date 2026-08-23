from dataclasses import dataclass
@dataclass
class Settings:
    profile:str="development"
    default_timeout:float=30
    max_retries:int=2
