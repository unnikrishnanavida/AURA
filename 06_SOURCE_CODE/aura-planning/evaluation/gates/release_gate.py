class ReleaseGate:
    def __init__(self,quality=.7): self.quality=quality
    def passes(self,report):
        return bool(report.get("feasible")) and bool(report.get("safe",True)) and report.get("quality",0)>=self.quality
