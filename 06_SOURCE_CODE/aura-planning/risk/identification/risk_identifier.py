class RiskIdentifier:
    def identify(self, plan, detectors):
        risks=[]
        for detector in detectors:
            risks.extend(detector.detect(plan))
        return tuple(risks)
