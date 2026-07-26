import unittest

from bus.dispatcher import Dispatcher
from bus.engine import BusEngine
from bus.events import BusEvent, BusEventBus
from bus.publisher import Publisher
from bus.subscriber import Subscriber


class BusEngineTests(unittest.TestCase):
    def test_register_and_execute_handler(self):
        engine = BusEngine()
        results = []

        def handler(event: BusEvent) -> str:
            results.append(event.payload.get("message"))
            return "ok"

        engine.register("test.event", handler)
        response = engine.publish("test.event", {"message": "hello"})

        self.assertEqual(results, ["hello"])
        self.assertEqual(response, ["ok"])

    def test_dispatcher_routes_events(self):
        dispatcher = Dispatcher()

        def handler(event: BusEvent) -> str:
            return event.payload.get("result", "none")

        dispatcher.register("dispatch.event", handler)
        response = dispatcher.dispatch("dispatch.event", {"result": "yes"})

        self.assertEqual(response, ["yes"])

    def test_publisher_subscribes_and_publishes(self):
        bus = BusEventBus()
        publisher = Publisher(event_bus=bus)
        received: list[BusEvent] = []

        def listener(event: BusEvent) -> None:
            received.append(event)

        publisher.subscribe("publish.event", listener)
        publisher.publish("publish.event", {"ok": True})

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload, {"ok": True})

    def test_subscriber_registers_listeners(self):
        bus = BusEventBus()
        subscriber = Subscriber(event_bus=bus)

        def listener(event: BusEvent) -> None:
            pass

        subscriber.register("subscribe.event", listener)
        self.assertEqual(subscriber.list(), ["subscribe.event"])


if __name__ == "__main__":
    unittest.main()
