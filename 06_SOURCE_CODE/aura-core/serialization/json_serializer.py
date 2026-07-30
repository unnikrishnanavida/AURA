import json


class JsonSerializer:
    def dumps(self, obj) -> bytes:
        return json.dumps(obj, default=str).encode("utf-8")

    def loads(self, data: bytes):
        return json.loads(data.decode("utf-8"))
