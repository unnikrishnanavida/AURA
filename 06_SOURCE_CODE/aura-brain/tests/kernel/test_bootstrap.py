import unittest

from kernel.state import Bootstrap


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_registers_expected_services(self):
        b = Bootstrap()
        container, context = b.bootstrap()

        # config must be registered
        config = container.resolve("config")
        self.assertIsInstance(config, dict)
        self.assertIn("env", config)

        # logger must be registered by the composition root
        logger = container.resolve("logger")
        import logging

        self.assertIsInstance(logger, logging.Logger)

        # runtime and manager should be available through the application composition root
        runtime = container.resolve("runtime")
        self.assertTrue(runtime.is_running())

        manager = container.resolve("runtime_manager")
        self.assertEqual(manager.state, "running")

        # cleanly shut down services after bootstrap
        b.shutdown()
        self.assertFalse(runtime.is_running())
        self.assertEqual(manager.state, "stopped")


if __name__ == "__main__":
    unittest.main()
