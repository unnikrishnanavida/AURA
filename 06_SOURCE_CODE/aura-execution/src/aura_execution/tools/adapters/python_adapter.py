from ..models.tool_output import ToolOutput


class PythonAdapter:
    def __init__(self, approved_executor=None):
        self.approved_executor = approved_executor

    def invoke(self, func, inputs, timeout=30):
        if self.approved_executor is None:
            return ToolOutput(False, error="python execution requires an approved executor")
        try:
            return ToolOutput(True, value=self.approved_executor(func, inputs, timeout))
        except Exception as exc:  # noqa: BLE001 - executor failures are tool failures
            return ToolOutput(False, error=str(exc))
