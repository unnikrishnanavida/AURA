def test_reasoning_router():
    from aura_planning.reasoning_bridge.contracts.reasoning_request import ReasoningRequest
    from aura_planning.reasoning_bridge.contracts.reasoning_result import ReasoningResult
    from aura_planning.reasoning_bridge.routing.strategy_router import StrategyRouter
    from aura_planning.reasoning_bridge.routing.reasoning_router import ReasoningRouter
    class S:
        def supports(self,r): return True
        def reason(self,r): return ReasoningResult(r.problem,1)
    result=ReasoningRouter(StrategyRouter([S()])).execute(ReasoningRequest("x"))
    assert result.conclusion=="x"
