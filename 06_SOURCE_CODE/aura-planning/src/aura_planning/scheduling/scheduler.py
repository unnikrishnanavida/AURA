from .temporal.temporal_scheduler import TemporalScheduler
class Scheduler:
    def __init__(self): self.temporal=TemporalScheduler()
    def schedule(self,tasks,dependencies=(),windows=None):
        return self.temporal.schedule(tasks,dependencies,windows)
