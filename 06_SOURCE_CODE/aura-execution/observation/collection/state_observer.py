class StateObserver:
    def detect(self,before,after):return {k:(before.get(k),after.get(k)) for k in set(before)|set(after) if before.get(k)!=after.get(k)}
