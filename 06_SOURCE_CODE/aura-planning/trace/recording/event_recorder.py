class EventRecorder:
    def __init__(self, recorder): self.recorder=recorder
    def record(self,event): return self.recorder.record(event.name,event.payload,event.level)
