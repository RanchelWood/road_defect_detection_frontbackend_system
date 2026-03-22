# Operations Runbook (Single VM, External Engine Integration)

This runbook defines v1 runtime operations with backend/frontend plus external inference engine integration.

## Deployment Topology

- One VM hosting backend and frontend services.
- External inference runtime for first engine (`rddc2020`) available via sibling path or sidecar container.
- Named volumes for SQLite and media artifacts.
- Job workspace directories for per-job engine execution outputs.

## Startup

1. Ensure `.env` exists from `.env.example`.
2. Start backend and frontend services.
3. Verify `rddc2020` runtime path and required weights are available.
4. Validate backend health and a dry-run engine command path check.

## Health and Observability Baseline

Required structured fields:

- `request_id`
- `job_id`
- `engine_id`
- `model_id`
- `route`
- `status`
- `duration_ms`
- `error_code`

Operational checks:

- Backend `/health` returns 200.
- Job creation endpoint accepts request and returns queued state.
- Polling endpoint transitions jobs to terminal states.
- Logs show command runtime and failures with context.

## Backup and Recovery (v1)

Daily backup scope:

- SQLite database volume.
- Media volume.
- Job artifact directories (if retained for debugging policy window).

Recovery steps:

1. Stop services.
2. Restore database and media/artifacts from backup.
3. Start services.
4. Verify auth, models, and history query.

## Engine Isolation Rules

- Run each inference job in unique working/output directory.
- Never reuse shared output directory across concurrent jobs.
- Do not execute arbitrary command arguments from clients.
- Restrict execution to allowlisted model presets.

## CPU and Optional GPU Runtime

Default is CPU-first. If GPU runtime is introduced later, keep API contract unchanged and benchmark per-engine latency deltas before rollout.

## Job Durability (Milestone 2B Hardening)

- On backend startup, pending jobs are reconciled from SQLite. Jobs in `running` are moved back to `queued` and annotated with `ENGINE_RECOVERED_RETRY`.
- If `INFERENCE_AUTORUN_ENABLED=true`, reconciled pending jobs are re-executed in startup order.
- Durability limit for this milestone: execution remains in-process/background-task based (not an external worker queue), so restart mid-execution can interrupt engine processes and requires requeue/retry handling.
- Startup replay currently runs inline during backend startup; large pending backlogs can increase boot time.
