# AURA Rollback Runbook

Migrations are **forward-only**. PostgreSQL/`schema_version` never downgrades.
Rollback must therefore be at the application + data level, never by "reverse
migrating" a production schema.

## Application rollback (no schema change)

1. Promote the previously deployed container image / wheel (previous release).
2. Verify `/ready` returns 200.
3. Verify `/health` dependency is OK.
4. Smoke-test one authenticated request.
5. Optionally keep the newer build's image on the node for forensics.

## Schema migrations are forward-only

`aura.memory.migrations` (SQLite) and `aura.memory.pg_migrations` (PostgreSQL)
are strictly forward. There is no downgrade path. Documented recovery for an
incompatible production schema:

1. **Never** alter the live schema to "downgrade" it.
2. Stop new application instances.
3. Restore the database from a verified backup made *before* the failed
   migration (see `docs/BACKUP_AND_RECOVERY.md`).
4. Start the compatible (older) application against the restored database.
5. Verify schema version == the compatible version and `/ready` is 200.
6. Verify data with a recall of a known memory key.

## Failed-release recovery flow

```
FAILED RELEASE
    |
    v
STOP NEW APPLICATION (scale/replace with old image)
    |
    v
RESTORE DATABASE FROM VERIFIED BACKUP (only if schema/data are broken)
    |
    v
START COMPATIBLE APPLICATION
    |
    v
VERIFY HEALTH (/ready == 200, /health dependency ok)
    |
    v
VERIFY DATA (recall known keys, check audit/provenance)
```

## Migration failure behavior (verified)

- A failed migration rolls back its transaction and raises `ConfigurationError`.
- A future/incompatible `schema_version` (e.g. current+100) causes startup
  refusal without mutating the row (verified in `tests/memory/test_pg_upgrade.py`).
- Concurrent multi-instance migrations are serialized by a PostgreSQL advisory
  lock (fixed in Phase 18; verified by `test_pg_concurrent_migration.py`).

## Data backups for rollback

- **SQLite**: `python -m aura.observability.backup_cli` produces atomic
  timestamped snapshots; restore refuses to clobber an open/live store.
- **PostgreSQL**: `aura.observability.pg_backup.create_pg_backup` produces
  deterministic SQL; `restore_pg_backup(..., force=True)` restores only AURA
  tables, refuses populated-target overwrite unless forced.

## Verification commands after any rollback

```bash
curl -fsS http://<host>/ready               # expect 200 {"status":"ready"}
curl -fsS http://<host>/health             # expect 200 {"status":"ok"}
# Authenticated request:
curl -fsS -X POST <host>/v1/reason -H 'Authorization: Bearer <key>' \
  -d '{"question":"smoke"}'
# Data check (SDK local or API):
python - <<'EOF'
from aura_sdk import AuraSDK, SdkConfig
sdk = AuraSDK(config=SdkConfig(mode=TransportMode.HTTP, endpoint="http://<host>", api_key="<key>"))
print(sdk.recall("rollback-check", limit=5))
EOF
```