class SafetyGate:
    def passes(self, report): return bool(report.get("safe"))
