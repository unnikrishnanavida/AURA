class ExecutionError(Exception): pass
class CapabilityDenied(ExecutionError): pass
class PermissionDenied(ExecutionError): pass
class SafetyDenied(ExecutionError): pass
class BudgetExceeded(ExecutionError): pass
class StateTransitionError(ExecutionError): pass
