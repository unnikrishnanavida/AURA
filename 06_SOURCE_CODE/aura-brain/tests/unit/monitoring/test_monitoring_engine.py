import unittest

from monitoring.engine import MonitoringEngine
from monitoring.events import MonitoringEvent
from monitoring.exceptions import MonitoringError
from monitoring.manager import MonitoringManager


def sample_handler(event: MonitoringEvent) -> dict[str, object]:
    return {"event_type": event.type, "payload": event.payload}


class MonitoringEngineTests(unittest.TestCase):
    def test_register_and_publish_handler(self):
        engine = MonitoringEngine()
        engine.register("health.check", sample_handler)

        result = engine.publish("health.check", {"check": "ok"})
        self.assertEqual(result, [{"event_type": "health.check", "payload": {"check": "ok"}}])

    def test_execute_unknown_handler_raises(self):
        engine = MonitoringEngine()

        with self.assertRaises(MonitoringError):
            engine.execute("missing")

    def test_manager_registers_and_publishes(self):
        manager = MonitoringManager()
        manager.register_handler("heartbeat", sample_handler)

        result = manager.publish_event("heartbeat", {"alive": True})
        self.assertEqual(result[0]["payload"], {"alive": True})


if __name__ == "__main__":
    unittest.main()
