import unittest

from plugins.exceptions import PluginsError
from plugins.manager import PluginsManager
from plugins.plugin import Plugin


class SamplePlugin(Plugin):
    def execute(self, *args, **kwargs):
        return {"echo": args, "kwargs": kwargs}


class PluginsManagerTests(unittest.TestCase):
    def test_register_and_execute_plugin(self):
        manager = PluginsManager()
        plugin = SamplePlugin(name="sample")

        manager.register("sample", plugin)
        self.assertEqual(manager.list(), ["sample"])

        result = manager.execute("sample", 1, 2, test=True)
        self.assertEqual(result, {"echo": (1, 2), "kwargs": {"test": True}})

    def test_unregister_plugin_and_fail(self):
        manager = PluginsManager()
        plugin = SamplePlugin(name="sample")
        manager.register("sample", plugin)
        manager.unregister("sample")

        with self.assertRaises(PluginsError):
            manager.execute("sample")


if __name__ == "__main__":
    unittest.main()
