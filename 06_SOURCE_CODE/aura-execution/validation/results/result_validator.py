from .outcome_validator import OutcomeValidator
from .expected_state_validator import ExpectedStateValidator
class ResultValidator:
    def __init__(self): self.outcome=OutcomeValidator();self.expected=ExpectedStateValidator()
    def validate(self,result,expected,observed):
        if not self.outcome.validate(result):return False,{"outcome":result.error}
        ok,m=self.expected.compare(expected,observed)
        return ok,m
