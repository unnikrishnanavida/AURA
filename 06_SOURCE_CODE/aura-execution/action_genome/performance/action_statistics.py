from dataclasses import dataclass
@dataclass
class ActionStatistics:
    runs:int=0;successes:int=0;total_duration:float=0
    @property
    def reliability(self):return self.successes/self.runs if self.runs else 0
