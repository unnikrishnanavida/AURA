import json
class TraceSerializer:
    def dumps(self,record):
        return json.dumps({"trace_id":record.trace_id,"events":[{"name":e.name,"timestamp":e.timestamp,"payload":e.payload,"level":e.level} for e in record.events],"metadata":record.metadata},sort_keys=True)
