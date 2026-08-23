import time
def benchmark(planner,cases):
    timings=[]
    for initial,goal in cases:
        start=time.perf_counter(); result=planner.plan(initial,goal); elapsed=time.perf_counter()-start
        timings.append({"success":bool(getattr(result,"success",result)),"seconds":elapsed})
    return {"cases":len(timings),"mean_seconds":sum(x["seconds"] for x in timings)/len(timings) if timings else 0.0,"results":tuple(timings)}
