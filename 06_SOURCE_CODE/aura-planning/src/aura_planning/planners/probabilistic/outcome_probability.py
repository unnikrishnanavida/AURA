class OutcomeProbability:
    def estimate(self,action,history=()):
        if history:
            successes=sum(bool(x) for x in history)
            return successes/len(history)
        return float(getattr(action,"outcome_probability",1.0))
