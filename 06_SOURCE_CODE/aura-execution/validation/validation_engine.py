from .results.result_validator import ResultValidator
class ValidationEngine:
    def __init__(self):self.validator=ResultValidator()
    def validate(self,result,expected,observed):return self.validator.validate(result,expected,observed)
