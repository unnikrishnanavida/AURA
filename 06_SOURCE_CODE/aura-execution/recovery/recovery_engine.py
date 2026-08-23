from .classification.failure_classifier import FailureClassifier
class RecoveryEngine:
    def __init__(self):self.classifier=FailureClassifier()
    def recommend(self,error,attempt,max_retries,reversible=False,fallback=False):
        f=self.classifier.classify(error)
        if f.transient and attempt<max_retries:return "retry"
        if reversible:return "rollback"
        if fallback:return "fallback"
        if f.policy:return "escalate"
        return "fail"
