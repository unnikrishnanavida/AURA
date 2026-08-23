class ResourceMonitor:
    def __init__(self,tracker):self.tracker=tracker
    def snapshot(self):return dict(self.tracker.used)
