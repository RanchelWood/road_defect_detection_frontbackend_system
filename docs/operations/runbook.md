# Operations Runbook (Single VM, Docker Compose)

This runbook defines the default deployment and runtime operations model for v1.

## Deployment Topology

- One VM hosting Docker Engine and Docker Compose.
- Services: `backend`, `frontend`, and optional reverse proxy.
- Named volumes: one for SQLite data and one for media files.

## Startup

1. Ensure `.env` exists from `.env.example`.
2. Run `docker compose -f infra/docker-compose.yml up -d --build`.
3. Verify service health.

## Health and Observability Baseline

Required structured log fields:

- `request_id`
- `route`
- `status_code`
- `duration_ms`
- `model_name` (for inference routes)
- `error_code` (for failures)

Operational checks:

- Backend health endpoint returns 200.
- Frontend page is reachable.
- Recent inference logs include timing metrics.

## Backup and Recovery (v1)

Daily backup scope:

- SQLite database file volume.
- Media volume (original and annotated images).

Recovery steps:

1. Stop services.
2. Restore database and media from backup snapshot.
3. Start services.
4. Verify health endpoint and a sample history query.

## CPU and Optional GPU Runtime

Default mode is CPU-only. If GPU is available later, enable a GPU-specific compose profile and verify inference latency improvements with the same benchmark image set.