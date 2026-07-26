import unittest

from gateway.exceptions import GatewayError
from gateway.request import GatewayRequest
from gateway.response import GatewayResponse
from gateway.router import Router
from gateway.validator import GatewayValidator


class GatewayRouterTests(unittest.TestCase):
    def test_register_and_dispatch_route(self):
        router = Router()

        def handler(request: dict[str, object]) -> GatewayResponse:
            return GatewayResponse(status="ok", data={"route": request["route"]})

        router.register("hello", handler)
        request = GatewayRequest(route="hello", payload={"value": 1})
        response = router.dispatch("hello", request.to_dict())

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.data, {"route": "hello"})

    def test_validator_rejects_empty_route(self):
        validator = GatewayValidator()

        with self.assertRaises(GatewayError):
            validator.validate_route("")

    def test_validator_rejects_invalid_request(self):
        validator = GatewayValidator()

        with self.assertRaises(GatewayError):
            validator.validate_request({"payload": {}})


if __name__ == "__main__":
    unittest.main()
