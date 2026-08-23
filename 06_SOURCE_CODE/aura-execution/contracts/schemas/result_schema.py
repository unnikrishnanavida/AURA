def validate_result_schema(result):
    if not result.execution_id: raise ValueError("execution id required")
    if result.status is None: raise ValueError("status required")
    return result
