REQUIRED_EXECUTION_FIELDS={"action","inputs"}
def validate_execution_payload(payload):
    missing=REQUIRED_EXECUTION_FIELDS-set(payload)
    if missing: raise ValueError(f"missing execution fields: {sorted(missing)}")
    return payload
