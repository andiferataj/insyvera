# Operations and deployment preparation

No cloud deployment is included in this task.

## Health

- /api/health: application process liveness.
- /api/ready: database/storage/queue readiness and actual provider/retrieval configuration.
- Compose worker check: `docker compose exec api python infrastructure/scripts/check_infrastructure.py`.
- Logs: `docker compose logs --tail 100 api worker`; local mode logs under .local.
- Broker failure is visible on the affected run/version; retry after recovery.

## Port ownership

Use the dedicated Compose project name insyvera. Defaults are 5180 (web) and 8100 (API), avoiding sibling-project database ports. Never reset Nexus/Velqora volumes.

## Migrations

`python -m alembic -c apps/api/alembic.ini upgrade head`.

The initial schema includes FTS and dimensioned pgvector/HNSW when PostgreSQL is selected. Future schema changes require a new migration. Do not change an embedding dimension in place without migrating and reindexing. For SQLite local mode, application startup creates absent initial tables.

## Backups

Local backup/restore is covered by an automated round-trip test. Stop the API/worker first so object files and checkpoints cannot change during the snapshot. Restore only into an empty directory.

Compose backup uses the PowerShell script in infrastructure/scripts. The script captures a PostgreSQL custom-format dump, MinIO's data tree and app checkpoints while application services are quiesced.

For an infrastructure restore:
1. Preserve the original stack and backup. Create a separate Compose project with fresh, empty named volumes and different loopback ports.
2. Start only PostgreSQL/Redis/MinIO. Restore the dump with pg_restore under the insyvera owner; apply migrations.
3. Stop MinIO before copying its complete backed-up data tree into the empty storage volume, preserving metadata and permissions. Restart MinIO.
4. Restore checkpoints into the new app volume under uid/gid 10001.
5. Start API/worker/web, run readiness/infrastructure checks and the complete demo/permission suite.
6. Only then choose whether to switch to the restored stack.

This procedure needs validation on the target Docker Desktop environment. Never overwrite the original volumes as a first restore attempt.

## Recovery

- Failed ingestion: inspect its error, fix/replace the source, then Reprocess.
- Missing formula caches: recalculate with Excel/LibreOffice and upload a new immutable version.
- Cancelled/failed research: Resume after its active node releases the per-run lock.
- Crashed running research: after 240 seconds, the API permits stale recovery. The checkpoint continues the pending stage.
- Model outage: a failed run exposes the error. Restore provider service and resume, or create a new extractive run.
- Chunk reprocessing/deletion: inspect unavailable-source warnings; saved prose is not silently rewritten.

## Observability

Set OTEL_EXPORTER_OTLP_ENDPOINT and start the observability profile for HTTP request traces. The included collector prints traces for local inspection. Structured logs include method/path/status/latency. There is no claim of a deployed monitoring service or production SLO.

## Deployment-day checklist

- [ ] Working Docker daemon; clean full-stack image build/start.
- [ ] Real PostgreSQL/pgvector/FTS, Redis/Celery and MinIO integration checks.
- [ ] Real Ollama/hosted-model and embedding smoke tests with chosen model IDs.
- [ ] Fresh-volume acceptance run on the target machine.
- [ ] Infrastructure backup and restore round trip.
- [ ] HTTPS, secure cookies, domain/origins, secret handling, signup policy.
- [ ] Cloud target and persistent-volume strategy chosen together.
- [ ] Re-run release gates, inspect limitations, then decide whether to tag v1.0.

A successful local test suite is not a substitute for these environment-specific gates.

## Deferred object cleanup

Logical deletion and physical object purging are separated by durable storage_deletions records. The Compose worker scheduler retries unfinished cleanup every 60 seconds. In lightweight local mode, after storage recovery run `python -m app.gc` to retry pending purges. Cleanup is idempotent; deleted document records do not become readable again during an outage.
