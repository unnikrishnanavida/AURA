from ..models.execution_failure import ExecutionFailure
class FailureClassifier:
    def classify(self,error):
        text=str(error).lower()
        return ExecutionFailure(str(error),transient=any(x in text for x in ("timeout","tempor","connection")),timeout="timeout" in text,policy=any(x in text for x in ("denied","permission","safety")),resource=any(x in text for x in ("budget","resource")))
