from enum import Enum
class RiskLevel(str,Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
def level(score):
    if score>=.9:return RiskLevel.CRITICAL
    if score>=.7:return RiskLevel.HIGH
    if score>=.4:return RiskLevel.MEDIUM
    return RiskLevel.LOW
