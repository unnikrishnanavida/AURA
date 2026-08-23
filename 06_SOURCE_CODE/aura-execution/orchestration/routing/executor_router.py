class ExecutorRouter:
    def route(self,action,executors):
        for executor in executors:
            if executor.supports(action):return executor
        return None
