try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional
    yaml = None


class YamlSerializer:
    def dumps(self, obj):
        if yaml is None:
            raise RuntimeError("pyyaml not installed")
        return yaml.dump(obj).encode("utf-8")

    def loads(self, data: bytes):
        if yaml is None:
            raise RuntimeError("pyyaml not installed")
        return yaml.safe_load(data.decode("utf-8"))
