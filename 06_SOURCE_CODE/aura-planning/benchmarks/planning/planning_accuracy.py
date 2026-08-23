def benchmark(planner,cases):
    results=[]
    for initial,goal,expected in cases:
        result=planner.plan(initial,goal)
        success=bool(getattr(result,"success",result))
        results.append(success==expected)
    return {"accuracy":sum(results)/len(results) if results else 0.0,"cases":len(results)}
