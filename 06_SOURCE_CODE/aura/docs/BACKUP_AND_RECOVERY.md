# AURA Backup and Recovery Runbook

Scope: persistent memory, configuration, audit data, and critical system
state. This documents what is implemented, verified, and how to operate it.
Nothing here is fabricated — every capability referenced has a regression test.

## What is backed up

| Data | SQLite | PostgreSQL |
| ---- | ------ | ---------- |
| memory entries (live + archive) | whole SQLite file | logical SQL export of `memory_entries` / `memory_archive` |
| schema version | embedded in file | `schema_version` table |
| sessions / keys / limits / audit / flight events | on-disk tables | in the same database as memory (included in PG backup) |

## Frequency / retention guidance

- **Frequency**: at least daily for staging; more frequently for production
  with significant write load. Backups are atomic timestamped snapshots.
- **Retention**: keep the most recent N backups (e.g. 7 daily + 4 weekly +
  12 monthly) — a documented operator choice, not enforced by a scheduler.
- **Off-site / encryption**: copy backup files to a second volume/zone;
  encryption-at-rest is delegated to the platform (volume/TDE). Do not rely
  on plaintext copies on the same disk as the database.

## Backup commands

SQLite:

```bash
python -m aura.observability.backup_cli \
  --db-path /data/aura.sqlite3 --backup-dir /data/backups \
  --instance-id api-1 --environment staging
```

PostgreSQL (deterministic psycopg-only export; no pg_dump required):

```python
from aura.observability.pg_backup import create_pg_backup
create_pg_backup(dsn="host=pg dbname=aura user=aura password=...",
                 backup_dir="/data/backups", instance_id="api-1", environment="production")
```

Manifest (`manifest.json` beside the backup) records instance, environment,
timestamp, method, and schema version.

## Restore procedure (PostgreSQL)

1. **Stop** new application instances writing to the target database.
2. Verify the backup file header declares the **current** schema version
   (`-- AURA logical backup ... schema_version=N`).
3. `restore_pg_backup(backup_path=..., dsn=..., force=False)` — refuses when
   the target already has memory rows unless `force=True` is passed.
4. Restore only drops/recreates AURA tables; user tables are untouched.
5. Start the application; verify `/ready` == 200 and `/health` dependency OK.
6. Verify data: recall a known memory key; check audit entries.

SQLite restore: `restore_backup(backup_path=..., db_path=...)` — the live
store must be closed first; the function rejects a locked file and refuses
schema-incompatible backups.

## Verify integrity after restore

- SQLite: `PRAGMA quick_check` runs inside `_quick_check` for every backup and
  restore.
- PostgreSQL: header schema-version parse + row-counts returned per table by
  `restore_pg_backup`; re-open the store and recall a known key.

## Disaster recovery runbook

```
1. DETECT      /ready returns 503; /health dependency ok=false; logs show
               persistence errors.
2. STOP        Scale application to zero (or point traffic at a standby).
3. RESTORE     Pick the latest verified backup; run the restore procedure.
4. VALIDATE    Schema version matches; known key recalls; audit non-empty.
5. START       Bring the application back; verify /ready and /health.
6. MONITOR     Watch error rate, latency, and memory-operation metrics for
               one hour; confirm no residual corruption.
```

## Failure cases verified by tests

- Corrupted backup file (non-AURA) rejected: `test_pg_backup_rejects_non_aura_file`.
- Restore into a populated target without `force`: refused.
- Incompatible schema version in backup: refused without touching data.
- Interrupted restore: the target is left in dropped-table state; re-run the
  restore to completion (idempotent re-creation via canonical migrations).
- SQLite restore of a live/locked store: refused.

## Scheduling examples (deployment examples only — not built-in schedulers)

- **cron**: `0 2 * * * cd /app && python -m aura.observability.backup_cli ...`
- **Kubernetes CronJob**: manifest invoking the same CLI in the aura image
  with a PG DSN from a Secret.
- These are provided so operators can wire their own scheduler; AURA does not
  silently invent or run a scheduler.

## Restore drills

Run a restore drill (Phase 16) at least once per release cycle against a
disposable database: create DB → write data → `create_pg_backup` → drop tables →
`restore_pg_backup` → verify data. `evaluation/production_topology_e2e.py` does
exactly this automatically.