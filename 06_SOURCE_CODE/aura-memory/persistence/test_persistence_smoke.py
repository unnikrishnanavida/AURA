import importlib.util
import os
import tempfile
import sys

# Load the persistence package directly from its __init__.py to avoid
# top-level package import name issues in this workspace layout.
here = os.path.dirname(__file__)
pkg_init = os.path.join(here, "__init__.py")
spec = importlib.util.spec_from_file_location("aura_memory.persistence", pkg_init)
persistence = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(persistence)
InMemoryStorage = persistence.InMemoryStorage
FileStorage = persistence.FileStorage
import time
import sys


def main():
    print("INMEMORY: start")
    s = InMemoryStorage(janitor_interval=0.1)
    s.set("k1", {"v": 1})
    assert s.get("k1") == {"v": 1}
    s.set("t", "x", ttl=0.3)
    time.sleep(0.4)
    assert s.get("t") is None
    print("INMEMORY: OK")

    print("FILE: start")
    d = tempfile.mkdtemp(prefix="aura_persist_test_")
    fs = FileStorage(d)
    fs.set("k2", {"v": 2})
    val = fs.get("k2")
    assert val == {"v": 2}
    print("FILE: GET OK", val)
    fs.set("t2", "y", ttl=0.2)
    time.sleep(0.25)
    assert fs.get("t2") is None
    print("FILE: TTL OK")
    keys = list(fs.list_keys())
    assert "k2" in keys
    fs.delete("k2")
    assert fs.get("k2") is None
    print("FILE: DELETE OK")

    print("ALL OK")

    # cleanup
    try:
        import shutil

        shutil.rmtree(d)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("TEST FAILED:", e)
        sys.exit(2)
    except Exception as e:
        import traceback

        traceback.print_exc()
        sys.exit(3)
    print("EXIT 0")
    sys.exit(0)
