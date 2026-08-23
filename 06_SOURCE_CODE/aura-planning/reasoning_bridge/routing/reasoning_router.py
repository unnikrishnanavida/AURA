class ReasoningRouter:
    def __init__(self, router):
        self.router = router
    def execute(self, request):
        request.validate()
        strategy = self.router.route(request)
        if strategy is None:
            raise LookupError("no reasoning strategy supports the request")
        return strategy.reason(request)
