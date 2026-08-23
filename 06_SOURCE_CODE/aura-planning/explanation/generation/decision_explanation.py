class DecisionExplanation:
    def explain(self,selected,candidates,score):
        ranked=sorted(candidates,key=score,reverse=True)
        return {
            "selected":selected,
            "ranking":tuple((candidate,score(candidate)) for candidate in ranked),
            "reason":"selected candidate has the highest supplied objective score",
        }
