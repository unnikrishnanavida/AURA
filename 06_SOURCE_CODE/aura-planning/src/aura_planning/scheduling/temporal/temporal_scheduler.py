from collections import defaultdict
class TemporalScheduler:
    def schedule(self,tasks,dependencies=(),windows=None):
        predecessors=defaultdict(set)
        for before,after,gap in dependencies:
            predecessors[after].add((before,gap))
        starts={}
        remaining=set(tasks)
        while remaining:
            ready=[t for t in remaining if all(p in starts for p,_ in predecessors[t])]
            if not ready: raise ValueError("temporal dependency cycle")
            for task in ready:
                start=max([starts[p]+getattr(tasks[p],"duration",0)+gap for p,gap in predecessors[task]] or [0])
                if windows and task in windows:
                    start=max(start,windows[task].start)
                    if start>windows[task].end: raise ValueError(f"task outside time window: {task}")
                starts[task]=start
                remaining.remove(task)
        return starts,{task:starts[task]+getattr(tasks[task],"duration",0) for task in tasks}
