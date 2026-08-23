class ResourceScheduler:
    def schedule(self,tasks,capacity):
        usage={}; starts={}
        for task in sorted(tasks,key=lambda t:getattr(t,"priority",0),reverse=True):
            req=getattr(task,"resources",{})
            if any(req.get(k,0)>capacity.get(k,0) for k in req):
                raise ValueError(f"task exceeds resource capacity: {task}")
            starts[task]=0
            for key,value in req.items(): usage[key]=usage.get(key,0)+value
        return starts,usage
