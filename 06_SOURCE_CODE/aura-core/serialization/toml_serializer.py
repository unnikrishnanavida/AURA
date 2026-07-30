try:
    import toml  # type: ignore
except Exception:  # pragma: no cover - optional
    toml = None


class TomlSerializer:
    def dumps(self, obj):
        if toml is None:
            raise RuntimeError("toml not installed")
        return toml.dumps(obj).encode("utf-8")

    def loads(self, data: bytes):
        if toml is None:
            raise RuntimeError("toml not installed")
        return toml.loads(data.decode("utf-8"))
