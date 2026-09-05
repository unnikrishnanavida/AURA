from urllib.request import Request, urlopen

from ..models.tool_output import ToolOutput


class HttpAdapter:
    def invoke(self, url, method="GET", timeout=10):
        try:
            with urlopen(Request(url, method=method), timeout=timeout) as r:
                return ToolOutput(True, value=r.read(), exit_code=getattr(r, "status", 200))
        except Exception as exc:  # noqa: BLE001 - network failures are tool failures
            return ToolOutput(False, error=str(exc))
