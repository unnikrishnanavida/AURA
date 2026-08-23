import importlib.util
import os
import tempfile

# import storage module by path
_here = os.path.dirname(__file__)
_path = os.path.join(_here, "__init__.py")
spec = importlib.util.spec_from_file_location("aura_memory.storage", _path)
storage = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(storage)


def test_sqlite_adapter():
    db_file = os.path.join(tempfile.gettempdir(), "aura_memory_test.db")
    try:
        adapter = storage.SQLiteAdapter(db_file)
        adapter.set("k1", {"a": 1})
        assert adapter.get("k1") == {"a": 1}
        adapter.set("ttl", "ok", ttl=0.1)
        import time

        time.sleep(0.15)
        assert adapter.get("ttl") is None
        adapter.delete("k1")
        assert adapter.get("k1") is None
    finally:
        adapter.close()
        try:
            os.remove(db_file)
        except Exception:
            pass


if __name__ == "__main__":
    test_sqlite_adapter()
    print("storage adapter tests passed")
