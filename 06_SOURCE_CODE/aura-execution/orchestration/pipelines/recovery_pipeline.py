class RecoveryPipeline:
    def __init__(self,recovery):self.recovery=recovery
    def run(self,error,attempt,max_retries,reversible=False,fallback=False):return self.recovery.recommend(error,attempt,max_retries,reversible,fallback)
