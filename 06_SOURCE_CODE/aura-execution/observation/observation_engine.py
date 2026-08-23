from .collection.observer import Observer
class ObservationEngine:
    def __init__(self):self.observer=Observer()
    def observe(self,before,after):return self.observer.observe(before,after)
