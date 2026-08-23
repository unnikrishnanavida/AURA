def validate_action_schema(action):
    if not action.action_id or not action.capability: raise ValueError("action identity/capability required")
    if action.timeout <= 0: raise ValueError("timeout must be positive")
    if action.max_retries < 0: raise ValueError("max_retries cannot be negative")
    return action
