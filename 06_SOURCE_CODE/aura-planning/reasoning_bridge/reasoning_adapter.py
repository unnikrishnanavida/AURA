class ReasoningAdapter:
    def __init__(self, router):
        self.router = router
    def reason(self, problem, context=None, constraints=(), metadata=None):
        from .contracts.reasoning_request import ReasoningRequest
        request = ReasoningRequest(problem, context, tuple(constraints), metadata or {})
        return self.router.execute(request)
