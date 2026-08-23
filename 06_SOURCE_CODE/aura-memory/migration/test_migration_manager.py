import importlib.util
import os
import sqlite3
import sys
import tempfile

# import migration module by path
_here = os.path.dirname(__file__)
_path = os.path.join(_here, "__init__.py")
spec = importlib.util.spec_from_file_location("aura_memory.migration", _path)
migration = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)


def test_migration_manager():
    db_file = os.path.join(tempfile.gettempdir(), "aura_memory_migration_test.db")
    try:
        manager = migration.MigrationManager(db_file)

        def script(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)")

        mig = migration.Migration(id="0001_create_test_table", description="create test table", script=script)
        manager.apply([mig])
        assert "0001_create_test_table" in manager.applied_ids()
        # second apply should be idempotent
        manager.apply([mig])
        assert manager.applied_ids().count("0001_create_test_table") == 1
    finally:
        manager.close()
        try:
            os.remove(db_file)
        except Exception:
            pass


if __name__ == "__main__":
    test_migration_manager()
    print("migration manager tests passed")
