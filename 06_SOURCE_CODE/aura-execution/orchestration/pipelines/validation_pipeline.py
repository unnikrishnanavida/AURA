class ValidationPipeline:
    def __init__(self,validator):self.validator=validator
    def run(self,result,expected,observed):return self.validator.validate(result,expected,observed)
