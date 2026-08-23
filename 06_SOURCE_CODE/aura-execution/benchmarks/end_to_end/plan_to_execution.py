def run(adapter,plan,executor):return [executor.execute(a) for a in adapter.to_execution_actions(plan)]
