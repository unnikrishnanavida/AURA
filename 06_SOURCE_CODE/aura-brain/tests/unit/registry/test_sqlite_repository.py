import os
import tempfile
import unittest

from registry.repository import SqliteRegistryRepository
from registry.models import RegistryEntry


class SqliteRepositoryTests(unittest.TestCase):
    def test_save_load_update_delete(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            repo = SqliteRegistryRepository(path)

            entry = RegistryEntry(name="item1", kind="test", data={"x": 1})
            repo.save(entry)

            loaded = repo.load("item1")
            self.assertEqual(loaded.name, "item1")
            self.assertEqual(loaded.data["x"], 1)

            entry.data["x"] = 2
            repo.update(entry)
            updated = repo.load("item1")
            self.assertEqual(updated.data["x"], 2)

            repo.delete("item1")
            with self.assertRaises(Exception):
                repo.load("item1")
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
