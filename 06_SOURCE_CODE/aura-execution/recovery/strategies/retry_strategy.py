class RetryStrategy:
    def choose(self,failure,attempt,max_attempts):
        return attempt<max_attempts and failure.transient
