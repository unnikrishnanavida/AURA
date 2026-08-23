def run(planner,adapter,executor,problem):
    plan=planner(problem);actions=adapter.to_execution_actions(plan);return [executor.execute(a) for a in actions]
