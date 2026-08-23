from aura_execution.safety.safety_engine import SafetyEngine
from aura_execution.actions.models.executable_action import ExecutableAction
from aura_execution.tools.adapters.shell_adapter import ShellAdapter
def test_high_risk_review():
    a=ExecutableAction("x","x","x",risk=.8)
    assert SafetyEngine().evaluate(a).decision=="REVIEW"
def test_shell_allowlist():
    r=ShellAdapter().invoke(["python","--version"])
    assert not r.success
