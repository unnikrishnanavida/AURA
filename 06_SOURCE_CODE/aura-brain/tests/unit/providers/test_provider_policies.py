import time
import unittest

from providers.provider import Provider
from providers.provider_config import ProviderConfig


class FlakyProvider(Provider):
    name = "flaky"

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        self._calls = 0

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health_check(self):
        return True

    def _run(self, payload=None, headers=None):
        self._calls += 1
        if self._calls < 2:
            raise RuntimeError("transient")
        return {"ok": True}


class ProviderPolicyTests(unittest.TestCase):
    def test_retry_and_protected_call(self):
        cfg = ProviderConfig(name="flaky", timeout=1, retries=2)
        p = FlakyProvider(cfg)

        res = p.execute(payload={})
        self.assertEqual(res, {"ok": True})


if __name__ == "__main__":
    unittest.main()
