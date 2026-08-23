from dataclasses import dataclass
@dataclass
class TimeBudget:
    limit:float; elapsed:float=0
    def consume(self,seconds):
        if self.elapsed+seconds>self.limit:return False
        self.elapsed+=seconds;return True
