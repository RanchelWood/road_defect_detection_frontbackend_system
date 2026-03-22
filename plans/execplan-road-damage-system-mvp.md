# Implement MVP-First Road Damage Defect System with External Inference Adapter Architecture

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `plans/PLANS.md`.

## Purpose / Big Picture

After this work, a beginner should be able to run a web system where a user can register, log in, choose a model, upload an image, submit an asynchronous inference job, and later view annotated results and history. In this revision, inference is not implemented directly in this repository. Instead, the system integrates an existing command-line runtime from `D:\road_defect_detection\rddc2020` through a dedicated inference adapter path. This keeps delivery practical now and preserves a clean extension point for additional inference systems later.

## Progress

- [x] (2026-03-21 00:00Z) Defined project preparation baseline and locked architecture defaults from PRD-aligned planning.
- [x] (2026-03-21 00:00Z) Created canonical living ExecPlan with mandatory sections and milestone structure.
- [x] (2026-03-22 03:30Z) Implemented Milestone 1 foundations: runnable FastAPI + React scaffolds, Dockerfiles, health endpoint, and auth flow baseline with tests.
- [x] (2026-03-22 06:20Z) Replanned Milestone 2 to integrate external `rddc2020` CLI instead of in-process inference implementation.
- [x] (2026-03-22 07:30Z) Milestone 2A completed: multi-engine adapter interfaces, auth-protected `/models`, async `/inference/jobs` contract, queued job persistence, and contract tests.
- [x] (2026-03-22 10:50Z) Milestone 2B integration completed: `rddc2020` adapter command execution path, async dispatch wiring, job state transitions, and persisted outputs/errors.
- [x] (2026-03-22 11:40Z) Milestone 2B post-review hardening completed: normalized job-result contract fields, idempotent SQLite backfill migration, adapter timeout classification, and startup queued/running reconciliation.
- [ ] Milestone 2C: implement job lifecycle persistence, history linkage, and status polling endpoints.
- [ ] Milestone 2D: implement frontend job submission, status polling, result rendering, and history navigation.
- [ ] Milestone 3: hardening (validation, observability, concurrency safety, integration tests).
- [ ] Milestone 4: Phase 2 real-time streaming design/implementation after stable image-job flow.
- [ ] Finalize Outcomes & Retrospective with achieved behavior, gaps, and lessons.

## Surprises & Discoveries

- Observation: `rddc2020` runtime side effects are global by default.
  Evidence: `D:\road_defect_detection\rddc2020\yolov5\detect.py` always writes `results.csv` in working directory and removes/recreates output folder passed by `--output`.

- Observation: first-engine candidate already has local weights and sample outputs in sibling folder.
  Evidence: `D:\road_defect_detection\rddc2020\yolov5\weights\IMSC\*.pt` and `D:\road_defect_detection\rddc2020\yolov5\inference\output\*.jpg` exist.

- Observation: direct in-process dependency merge between web backend and `rddc2020` would be high risk.
  Evidence: `rddc2020` YOLOv5 stack has separate dependency profile and command assumptions centered on its own working directory.

- Observation: startup reconciliation currently replays pending jobs inline when autorun is enabled.
  Evidence: `backend/app/main.py` calls `InferenceJobService().recover_pending_jobs_on_startup()`, and `backend/app/services/inference_jobs.py` executes recovered jobs synchronously in a loop.

## Decision Log

- Decision: Use external `rddc2020` command-line integration for Milestone 2 instead of implementing native inference in this repo.
  Rationale: Fastest path to deliver image inference behavior with validated existing models.
  Date/Author: 2026-03-22 / Codex

- Decision: Keep backend API asynchronous for inference (`jobs` model) rather than synchronous request/response inference.
  Rationale: Avoid HTTP blocking and enable resilient status tracking for longer-running CLI operations.
  Date/Author: 2026-03-22 / Codex

- Decision: Introduce multi-engine adapter abstraction now, with `rddc2020` as first engine.
  Rationale: Prevent hard-coupling to one inference runtime and reduce future migration cost.
  Date/Author: 2026-03-22 / Codex

- Decision: Preserve image-only scope for this phase; defer video/WebSocket behavior.
  Rationale: Keeps milestone risk manageable while integrating external runtime safely.
  Date/Author: 2026-03-22 / Codex

- Decision: Use static in-code model presets and queued-only dispatcher in Milestone 2A.
  Rationale: Delivers stable contracts first while deferring real engine execution to Milestone 2B.
  Date/Author: 2026-03-22 / Codex

- Decision: Normalize detection payload fields at API boundary (`confidence`, `bbox`, `image_refs`) for all succeeded jobs, including legacy stored results.
  Rationale: Prevent contract drift between persisted adapter outputs and declared OpenAPI schema while preserving backward compatibility.
  Date/Author: 2026-03-22 / Codex

- Decision: Add startup reconciliation for `queued`/`running` jobs and classify adapter hangs as `ENGINE_TIMEOUT`.
  Rationale: Minimal durability and failure semantics are required before introducing external worker infrastructure.
  Date/Author: 2026-03-22 / Codex

- Decision: Keep startup replay in-process for Milestone 2B and document boot-time tradeoffs.
  Rationale: Delivers restart recovery now without introducing a queue service in the same milestone.
  Date/Author: 2026-03-22 / Codex

## Outcomes & Retrospective

This section must be updated at each milestone completion. At full completion, summarize delivered user-visible behavior, unresolved gaps, and lessons for v2 multi-engine scaling.

Milestone 2A outcome (2026-03-22): backend now exposes auth-protected model listing and async inference job contract with queued persistence. Remaining work moves to Milestone 2B for real `rddc2020` command execution and status transitions beyond queued.

Milestone 2B integration outcome (2026-03-22): backend now executes `rddc2020` through per-job isolated workspace/output paths and transitions jobs `queued -> running -> succeeded/failed` with persisted result/error metadata.

Milestone 2B hardening outcome (2026-03-22): job detail payloads now normalize to the declared detection schema, SQLite startup migration backfills Milestone 2B columns safely for older databases, adapter execution has explicit timeout classification, and startup reconciles queued/running jobs with documented durability limits.

## Context and Orientation

Current state includes a working Milestone 1 auth + health scaffold in `backend/` and `frontend/`. The inference runtime that will be integrated is in sibling directory `D:\road_defect_detection\rddc2020`, with its primary script at `D:\road_defect_detection\rddc2020\yolov5\detect.py`.

In this repository, an inference engine means an implementation that can execute inference jobs and return normalized outputs. An inference adapter means the backend interface layer that maps generic job requests into engine-specific execution details.

The first engine is `rddc2020-cli`. Future engines (for example, other YOLO repos or model servers) must be addable without changing frontend API contracts.

## Plan of Work

Milestone 2A defines adapter contracts and async job API shapes. Add backend service interfaces for model registry, job dispatch, and result normalization with explicit engine boundary.

Milestone 2B is complete. `rddc2020` execution now runs in per-job isolated workspace/output directories so `results.csv` and output paths do not collide across jobs. Current runtime uses in-process execution with startup reconciliation; external worker/queue is deferred to later hardening.

Milestone 2C implements persistence and retrieval. Store job status transitions (`queued`, `running`, `succeeded`, `failed`) and history metadata tied to user and model. Surface results through job detail and history endpoints.

Milestone 2D updates frontend behavior. Replace sync inference submission with job create + polling flow, render queued/running states, and display final annotated output and detections.

## Concrete Steps

All commands below are run from repository root `D:\road_defect_detection\frondend-backend-system` unless stated otherwise.

Backend and frontend baseline (already completed):

    cd backend
    python -m pytest tests

    cd ..\frontend
    npm run build

Planned integration checks for Milestone 2:

    # from sibling runtime
    cd D:\road_defect_detection\rddc2020\yolov5
    python detect.py --weights weights/IMSC/last_95.pt --img 640 --source <job_input_path> --output <job_output_path> --conf-thres 0.20 --iou-thres 0.9999 --agnostic-nms --augment

Expected observable output for a successful job:

    - Annotated image written into unique job output directory.
    - CSV row(s) emitted for detections in job-specific working directory.
    - Backend job status transitions: queued -> running -> succeeded.

## Validation and Acceptance

Milestone 2 is accepted when a user can submit image inference job, receive `job_id`, observe status transitions through polling, and view final result/history linked to their account.

Validation must prove:

- Concurrent jobs do not overwrite each other's outputs.
- Invalid model selection fails with documented error codes.
- Engine execution failure is surfaced as `failed` job with error metadata.
- API contracts remain stable for adding second engine later.

## Idempotence and Recovery

Job submission must be idempotent at API and storage boundaries where practical. If engine execution fails midway, job transitions to `failed` with retained input and error context for debugging. Recovery path is retry via new job submission. Cleanup policies must not delete unrelated job artifacts.

## Artifacts and Notes

Maintain these artifacts during implementation:

    docs/contracts/openapi.yaml
    docs/contracts/model-registry.md
    docs/architecture/system-architecture.md
    docs/architecture/data-model.md
    docs/operations/runbook.md

Capture concise evidence snippets after milestone implementation:

    POST /inference/jobs -> { job_id, status: queued }
    GET /inference/jobs/{job_id} -> status transitions and final result payload
    concurrent test run demonstrating isolated outputs

## Interfaces and Dependencies

Define backend interfaces as stable extension seams:

In `backend/app/services/adapters/base.py`, define:

    class InferenceEngineAdapter:
        engine_id: str
        def list_models(self) -> list[ModelPreset]: ...
        def run(self, input_image_path: str, job_workspace: str, model: ModelPreset) -> AdapterExecutionResult: ...

    class AdapterExecutionError(Exception):
        code: str
        message: str

In `backend/app/services/dispatcher.py`, define:

    class InferenceDispatcher:
        def dispatch(self, background_tasks: BackgroundTasks, job_id: str, execute_fn: Callable[[str], None]) -> None: ...

In `backend/app/services/inference_jobs.py`, define:

    class InferenceJobService:
        def create_queued_job(...): ...
        def dispatch_job(...): ...
        def execute_job(self, job_id: str) -> None: ...
        def recover_pending_jobs_on_startup(self) -> None: ...

The first adapter implementation targets `rddc2020-cli`; additional engines must implement the same interface without contract changes to frontend endpoints.

---

Plan change note (2026-03-21 / Codex): Initial creation of the living ExecPlan from PRD and master preparation plan.
Plan change note (2026-03-22 / Codex): Executed Milestone 1 scaffolding with runnable health/auth flow.
Plan change note (2026-03-22 / Codex): Pivoted Milestone 2 to external `rddc2020` async integration with multi-engine adapter-first design.
Plan change note (2026-03-22 / Codex): Implemented Milestone 2A backend scaffolding (adapter interfaces, models endpoint, jobs endpoint, queued persistence, and tests passing).
Plan change note (2026-03-22 / Codex): Applied Milestone 2B hardening fixes for contract alignment, SQLite migration safety, timeout classification, and restart reconciliation with tests.
Plan change note (2026-03-22 / Codex): Reviewed Milestone 2B patch after delegation (`@Ptolemy`), re-ran backend tests (`16 passed`), and aligned progress/operations docs.
