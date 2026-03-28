# Operations Runbook (Single VM, External Engine Integration)

This runbook defines v1 runtime operations with backend/frontend plus external inference engine integration.

## Deployment Topology

- One VM hosting backend and frontend services.
- External inference runtimes integrated via adapter layer.
- Active image engines:
  - `rddc2020-cli`
  - `orddc2024-cli`
  - `shiyu-grddc2022-cli`
- Named volumes for SQLite and media artifacts.
- Job workspace directories for per-job engine execution outputs.

## Startup

1. Ensure `.env` exists from `.env.example`.
2. Start backend and frontend services.
3. Verify `rddc2020` runtime path and required weights are available.
4. Verify `orddc2024` runtime path, python environment, and `models_ph1/models_ph2` caches.
5. Verify `shiyu-grddc2022` runtime path and required scripts/weights (`yolov7/detect.py`, `yolov5/detect.py`, `merge.py`, `YOLOv7x_640.pt`, `YOLOv5x_640.pt`).
6. Validate backend health and a dry-run model listing check (`GET /models`).

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
- `/models` includes all active engine families.
- Job creation endpoint accepts valid image request and returns queued state.
- Invalid or mismatched image bytes are rejected with `INVALID_IMAGE_CONTENT`.
- Polling endpoint transitions jobs to terminal states (`succeeded`, `failed`, `cancelled`).
- Cancel endpoint (`POST /inference/jobs/{job_id}/cancel`) updates queued/running jobs safely.
- Multi-engine safety: engine-specific runtime failures are isolated by adapter and should not block other engine models.
- Logs show lifecycle events (`inference_job_created/claimed/succeeded/failed/cancelled`) with request/job context.

## Backup and Recovery (v1)

Daily backup scope:

- SQLite database volume.
- Media volume.
- Job artifact directories (if retained for debugging policy window).

Recovery steps:

1. Stop services.
2. Restore database and media/artifacts from backup.
3. Start services.
4. Verify auth, models, inference polling, and history queries.

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

## Client Image Access (BUG-20260322-003)

- API consumers must fetch job images via authenticated endpoint `GET /inference/jobs/{job_id}/image/{kind}`.
- Filesystem paths in job payloads are backend-internal references and are not reliable browser URLs.

## ORDDC2024 Runtime Preflight (Active)

Use this checklist for second-engine reliability:

- `orddc2024` root path exists and contains phase scripts.
- Configured python executable points to dedicated env: `D:\anaconda3\envs\orddc2024\python.exe` (or equivalent via env var override).
- `models_ph1` and `models_ph2` folders are present (production default: pre-provisioned; no on-demand download).
- Runtime can write per-job `image_root`, `results.csv`, `boxed_output`, and run log files.
- Warnings in stderr alone (for example `pkg_resources` deprecation) do not count as job failure when exit code and output checks pass.
- Availability verification must use a valid decodable image file, not placeholder bytes.

## ShiYu GRDDC2022 Runtime Preflight (Active)

Use this checklist for third-engine reliability:

- `shiyu_grddc2022_root` exists and includes `yolov7/detect.py`, `yolov5/detect.py`, and `merge.py`.
- Configured python executable points to dedicated env: `D:\anaconda3\envs\crddc2022\python.exe` (or override via env var).
- Required weights exist:
  - `yolov7/YOLOv7x_640.pt`
  - `yolov5/YOLOv5x_640.pt`
- `yolov5/data/rdd.yaml` exists for YOLOv5 command.
- Preset-specific timeout values are tuned (`SHIYU_GRDDC2022_TIMEOUT_SECONDS_SINGLE`, `SHIYU_GRDDC2022_TIMEOUT_SECONDS_ENSEMBLE`).
- Ensemble final annotated image is generated from merged detections (not child-model overlay reuse).
- If `Pillow` is unavailable, adapter falls back to copying original image so job completion is not blocked (overlay drawing is skipped).

## Video Inference Preflight (Planned Phase 4A)

Use this checklist before enabling async video jobs:

- Video decode/render toolchain is available (for example ffmpeg/opencv path used by implementation).
- Upload limits are configured (max size and max duration) for CPU-safe operation.
- Temporary frame directories are writable and cleanup policy is configured.
- Concurrency cap for video jobs is set to avoid CPU starvation.
- Default video model is set to a speed-oriented preset (`orddc2024-phase2-ensemble`).

## Streaming Preflight (Planned Phase 4B)

- WebSocket endpoint auth verification is enabled.
- Stream-capable models are explicitly marked in registry metadata.
- Backpressure policy exists for slow clients.
- Async video fallback path remains available when WebSocket session fails.

## Planning References

- `docs/architecture/orddc2024-integration-design.md`
- `docs/architecture/shiyu-grddc2022-integration-design.md`
- `docs/architecture/video-support-design.md`
- `docs/contracts/video-inference-job-contract.md`

## Known local test-run caveat

- In this Codex desktop runtime, full backend `pytest tests` runs that rely on tmp-path fixtures may hit `PermissionError: [WinError 5]` under pytest temp roots.
- Team workflow gate for Milestone 3 uses targeted backend suites for verification when this environment constraint appears.
- For Milestone 3E adapter tests, even isolated `--basetemp` runs can still fail during pytest tmpdir cleanup with `PermissionError: [WinError 5]` in this sandbox.
- Frontend Vitest/Playwright startup in this sandbox can fail before runner execution with `EPERM: operation not permitted, lstat 'C:\Users\18926'`; use a local host shell for closure evidence when this occurs.
