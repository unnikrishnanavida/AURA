def pipeline(request,planner,evaluator):
    plan=planner.plan(request)
    return {"plan":plan,"evaluation":evaluator.evaluate(plan)}
