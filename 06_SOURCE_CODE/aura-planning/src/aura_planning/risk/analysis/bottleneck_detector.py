class BottleneckDetector:
    def find(self,plan):
        actions=tuple(getattr(plan,"actions",plan))
        return tuple(sorted(actions,key=lambda a:getattr(a,"duration",0)*max(1,getattr(a,"risk",0)),reverse=True))
