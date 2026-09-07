"""Backup command for persistent AURA data.

Usage:
    python -m aura.observability.backup_cli <db_path> <backup_dir> [--instance=...] [--environment=...]

Exit codes: 0 success, 1 backup failure, 2 usage error.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AURA SQLite backup")
    parser.add_argument("db_path", help="path to the live SQLite database")
    parser.add_argument("backup_dir", help="directory to write the backup + manifest")
    parser.add_argument("--instance", default="default")
    parser.add_argument("--environment", default="development")
    args = parser.parse_args(argv)

    from aura.observability.backup import BackupError, create_backup

    try:
        result = create_backup(
            db_path=args.db_path,
            backup_dir=args.backup_dir,
            instance_id=args.instance,
            environment=args.environment,
        )
    except BackupError as exc:
        print(f"BACKUP FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"backup written: {result.path} ({result.size_bytes} bytes, schema v{result.schema_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())