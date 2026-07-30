class BinarySerializer:
    def dumps(self, obj) -> bytes:
        # placeholder: use pickle or protobuf in real implementations
        import pickle

        return pickle.dumps(obj)

    def loads(self, data: bytes):
        import pickle

        return pickle.loads(data)
