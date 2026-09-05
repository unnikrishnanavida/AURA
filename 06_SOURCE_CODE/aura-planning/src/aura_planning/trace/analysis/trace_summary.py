class TraceSummary:
    def summarize(self,record):
        return {"trace_id":record.trace_id,"events":len(record.events),
                "errors":sum(e.level=="error" for e in record.events),
                "warnings":sum(e.level=="warning" for e in record.events)}
