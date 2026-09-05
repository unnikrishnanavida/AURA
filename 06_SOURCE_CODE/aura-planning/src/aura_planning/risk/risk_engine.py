from .identification.risk_identifier import RiskIdentifier
from .analysis.risk_analyzer import RiskAnalyzer
from .mitigation.risk_mitigator import RiskMitigator
class RiskEngine:
    def __init__(self, detectors=()):
        self.identifier=RiskIdentifier()
        self.analyzer=RiskAnalyzer()
        self.mitigator=RiskMitigator()
        self.detectors=tuple(detectors)
    def assess(self, plan):
        risks=self.identifier.identify(plan,self.detectors)
        return self.analyzer.assess(risks)
    def mitigate(self, risks, mitigations):
        return self.mitigator.mitigate(risks,mitigations)
