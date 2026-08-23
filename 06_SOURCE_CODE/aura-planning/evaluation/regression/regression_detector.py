class RegressionDetector:
    def compare(self, baseline, current, tolerance=.05):
        changes={}
        for key in set(baseline)|set(current):
            old=baseline.get(key); new=current.get(key)
            if isinstance(old,(int,float)) and isinstance(new,(int,float)) and old!=0:
                delta=(new-old)/abs(old)
                if abs(delta)>tolerance: changes[key]={"baseline":old,"current":new,"relative_change":delta}
        return changes
