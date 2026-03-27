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
- [x] (2026-03-22 12:30Z) Milestone 2C backend completed: `/history` user-scoped pagination/filtering, computed history stats, and polling-readiness preserved on `/inference/jobs/{job_id}`.
- [x] (2026-03-22 12:45Z) Milestone 2C independently reviewed in main workflow; backend tests re-run and passing (`19 passed`).
- [x] (2026-03-22 13:40Z) Milestone 2D frontend completed: protected `/inference` + `/history` routes, async submit/polling UI, result/detection rendering, and paginated history navigation.
- [x] (2026-03-22 14:05Z) Milestone 2D independently reviewed in main workflow; frontend build re-run and passing (`npm run build`).
- [x] (2026-03-22 15:00Z) Workflow governance update completed: added Test Engineer thread role, bug lifecycle states, and standard bug-report/assignment/retest templates.
- [x] (2026-03-22 16:10Z) Post-M2D bugfix cycle closed: `BUG-20260322-001` and `BUG-20260322-002` triaged to frontend, fixed via delegated FE patch, independently build-validated, and passed Test Engineer retest before closure.
- [x] (2026-03-23 02:45Z) Post-closure regression stabilization completed: timer-anchor timezone skew and polling overlap starvation were fixed (BUG-20260322-001/002 reopened then re-closed), with backend UTC timestamp serialization and frontend non-overlapping polling.
- [x] (2026-03-23 06:10Z) Milestone 3 QA workflow preparation completed: adopted planned frontend automation stack targets, updated engineering workflow docs, and briefed Test Engineer thread expectations.
- [x] (2026-03-23 09:20Z) Milestone 3A implementation completed: frontend Vitest + Playwright automation was wired (configs/scripts/tests), environment compatibility was stabilized (jsdom pin), and quality gates were validated (`test:unit`, `test:e2e:smoke`, `npm run build`).
- [x] (2026-03-24 08:40Z) Milestone 3B history-management UX/API completed: added user-scoped delete-one and clear-all history operations, /history page-size selector (10/20/50), frontend/unit/backend test coverage, and passing validation gates.
- [x] (2026-03-25 03:20Z) Workflow ownership optimized: Test Engineer now executes required test suites and submits command/artifact evidence; Team Leader is evidence supervisor and closure gate keeper.
- [x] (2026-03-25 07:40Z) Feature batch completed: inference model selection now persists across refresh, users can cancel queued/running jobs, and history supports time/id/name sorting with asc/desc order.
- [x] (2026-03-25 09:10Z) UX enhancement batch completed: history cards now show picture title + model name line, and GUI now supports persistent light/dark theme switching.

- [x] (2026-03-25 10:35Z) Documentation synchronization pass completed: audited all project-owned Markdown files and aligned API/UX/ops/workflow docs with implemented Milestone 2 behavior.
- [x] (2026-03-26 07:25Z) Second-engine planning assessment completed for orddc2024: consulted integration report/runtime scripts and documented the implementation blueprint (no code changes).
- [x] (2026-03-26 10:10Z) Video-support feasibility and roadmap planning completed: consulted ORDDC2024 video report and documented async-first video contract/design updates (no code changes).
- [x] (2026-03-26 13:20Z) Milestone 3C implemented: ORDDC2024 adapter integrated (`orddc2024-cli`), model registry expanded, config/env defaults added, and backend tests passed.
- [x] (2026-03-26 13:40Z) Milestone 3C runtime availability verified by Test Engineer with real ORDDC image inference (`orddc2024-phase2-ensemble`) succeeding end-to-end.
- [x] (2026-03-26 13:55Z) Milestone 3D completed: inference GUI updated for multi-engine model selection (engine-family filter + grouped model options), with unit and smoke verification passed by Test Engineer.
- [x] (2026-03-26 14:45Z) Post-release ORDDC runtime bug fixed: adapter now passes absolute workspace paths to ORDDC scripts and surfaces traceback-tail errors; Test Engineer verified both Phase1 and Phase2 succeed end-to-end.
- [x] (2026-03-27 09:08Z) Milestone 3 hardening completed: strict image-content validation, structured inference lifecycle logging, atomic queued-claim/success-finalization guards, and backend integration regressions updated with passing Test Engineer evidence (`28 passed`).
- [x] (2026-03-27 09:46Z) Confidence UI policy implemented: confidence/max-confidence display removed from frontend inference/history views, while backend confidence field is retained for forward compatibility.
- [x] Milestone 3: hardening (validation, observability, concurrency safety, integration tests).
- [x] Milestone 3C: ORDDC2024 second-engine integration using existing adapter contracts and async job APIs.
- [ ] Milestone 4A: async video inference jobs (`create + poll + cancel`) with video-specific result metadata.
- [ ] Milestone 4B: optional WebSocket streaming for near-real-time inference after Milestone 4A stabilizes.
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

- Observation: SQLite datetime roundtrip can return timezone-naive values at API boundary unless normalized before serialization.
  Evidence: inference timer showed 480:00 in UTC+8 locale when frontend interpreted naive timestamps as local-time anchors.


- Observation: ORDDC2024 runtime scripts expect directory input/output contracts, not single-image file paths.
  Evidence: `inference_script_v2_Phase1.py` and `inference_script_v2_Phase2.py` require `<images_path> <output_csv> [output_images_dir]` arguments.

- Observation: ORDDC2024 successful runs can still emit warnings on stderr.
  Evidence: `run_log.md` and `run_log_phase2_bash.md` include `pkg_resources` warnings while producing valid CSV and boxed outputs.

- Observation: ORDDC2024 Phase 1 is runtime-heavy on CPU because of a large ensemble set.
  Evidence: Phase 1 log shows 15-model loading and about 22 seconds elapsed for one sample image on CPU.

- Observation: ORDDC2024 runtime is image-oriented, and current scripts do not provide a complete video-native output contract.
  Evidence: `VIDEO_INFERENCE_SUPPORT_REPORT.md` documents that pipeline assumptions remain image-style and require frame extraction/aggregation for this project.

- Observation: ORDDC2024 Phase 2 ensemble is materially faster than Phase 1 and is the better candidate for planned video workloads.
  Evidence: `VIDEO_INFERENCE_SUPPORT_REPORT.md` benchmark notes show Phase 2 lower end-to-end latency versus Phase 1 under comparable CPU conditions.

- Observation: ORDDC runtime availability checks must use a real decodable image file; fake bytes produce downstream YOLO loader assertion failures.
  Evidence: Test Engineer reproduced `AssertionError: Image Not Found ...input.jpg` when submitting placeholder bytes, and confirmed success when re-running with `Japan_012698.jpg`.

- Observation: this machine's working ORDDC python runtime is `D:\anaconda3\envs\orddc2024\python.exe`.
  Evidence: Test Engineer end-to-end Phase2 job succeeded only after aligning backend config/env to the dedicated `orddc2024` conda environment.

- Observation: ORDDC scripts fail when backend passes relative `image_root/results/boxed_output` paths while `cwd` is ORDDC root.
  Evidence: failed run logs showed `ValueError: Invalid path to images` for `media\inference_jobs\...\runtime\image_root`, which resolved after switching command args to absolute paths.

- Observation: local full-backend pytest runs that use tmp-path fixtures can fail in this Codex runtime due Windows temp-directory permission constraints, even when Milestone 3 hardening tests pass.
  Evidence: Test Engineer runs showed targeted suites passing (`28 passed`) while full suite errored on `PermissionError: [WinError 5]` under `.pytest_tmp_run/pytest-of-18926`.

- Observation: both active image engines currently emit integration CSV outputs as class+bbox tuples without confidence values.
  Evidence: `D:\road_defect_detection\rddc2020\yolov5\detect.py` and ORDDC phase scripts write CSV rows without confidence fields, and adapters normalize detections with `confidence: null`.
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

- Decision: History statistic extraction must degrade safely on malformed or legacy detection payloads.
  Rationale: Persisted detections can vary by engine/runtime version; history endpoint should remain stable and non-failing.
  Date/Author: 2026-03-22 / Codex

- Decision: Frontend must show a clear fallback message when annotated image references are non-web-renderable filesystem paths.
  Rationale: Current backend returns local paths; explicit messaging avoids broken image UI while preserving operator visibility.
  Date/Author: 2026-03-22 / Codex

- Decision: Adopt a verification-gated bug lifecycle managed by Team Leader with a dedicated Test Engineer thread.
  Rationale: Keeps MVP debugging structured and beginner-friendly while preventing unverified closures.
  Date/Author: 2026-03-22 / Codex

- Decision: Frontend job polling state must ignore stale out-of-order responses, and live elapsed timer display must remain strict `mm:ss`.
  Rationale: Prevents terminal-state UI desync after async polling and enforces the approved UX display contract.
  Date/Author: 2026-03-22 / Codex

- Decision: Job timestamp payloads must be serialized with explicit UTC timezone (Z), and frontend timestamp parsing must treat missing timezone as UTC for backward compatibility.
  Rationale: Prevents locale-dependent elapsed-time drift and keeps timer behavior stable across refresh and timezones.
  Date/Author: 2026-03-23 / Codex

- Decision: Polling must be non-overlapping to avoid response starvation on slow requests.
  Rationale: Ensures terminal-state updates are eventually applied without requiring manual browser refresh.
  Date/Author: 2026-03-23 / Codex

- Decision: Frontend QA automation standard will use Vitest v4.1.0 for unit/component coverage and Playwright v1.58.2 for browser E2E smoke/regression coverage.
  Rationale: Combines fast local feedback with reproducible end-to-end evidence for triage, retest, and release confidence.
  Date/Author: 2026-03-23 / Codex

- Decision: History mutation APIs are account-scoped with explicit endpoints (DELETE /history/{job_id}, DELETE /history) and frontend page-size control is constrained to 10/20/50 with page reset to 1 on size/filter changes.
  Rationale: Meets user-requested data management features while preserving auth safety and predictable pagination UX.
  Date/Author: 2026-03-24 / Codex

- Decision: Test execution ownership is delegated to Test Engineer, while Team Leader supervises evidence quality and closure readiness.
  Rationale: Prevents report-only QA behavior and enforces reproducible verification before closure.
  Date/Author: 2026-03-25 / Codex

- Decision: Running-job cancellation will use cooperative adapter termination plus explicit `cancelled` terminal status to preserve async contract while allowing user-triggered stop.
  Rationale: Supports safe cancellation semantics for queued and running jobs without breaking existing polling-based UI flows.
  Date/Author: 2026-03-25 / Codex

- Decision: History sorting contract now includes `sort_by=time|id|name` and `sort_order=asc|desc`, and inference model selection persists via frontend local storage.
  Rationale: Delivers requested usability controls (refresh persistence + flexible history ordering) while keeping API/UI state URL-driven and testable.
  Date/Author: 2026-03-25 / Codex

- Decision: History list items now expose `original_filename` and frontend cards prioritize it as the display title, while model name text is resolved from model registry metadata with `model_id` fallback.
  Rationale: Aligns card content with user mental model (image-first context + explicit chosen model) without breaking history API compatibility.
  Date/Author: 2026-03-25 / Codex

- Decision: Theme system uses persisted class-based light/dark switching at app root with reusable toggle controls in both auth pages and authenticated shell.
  Rationale: Delivers requested dark theme UX with minimal refactor and stable cross-page behavior.
  Date/Author: 2026-03-25 / Codex

- Decision: Integrate ORDDC2024 through the existing async jobs API by mapping phase selection into model presets (`orddc2024-phase1-ensemble`, `orddc2024-phase2-ensemble`).
  Rationale: Preserves frontend/API compatibility while enabling second-engine support with minimal surface change.
  Date/Author: 2026-03-26 / Codex

- Decision: Use direct python executable invocation for ORDDC2024 adapter process management instead of Git Bash shell wrapping.
  Rationale: Matches current adapter architecture and keeps timeout/cancellation/error handling deterministic.
  Date/Author: 2026-03-26 / Codex

- Decision: ORDDC2024 integration will default to pre-provisioned model caches (`models_ph1`/`models_ph2`) and fail fast when missing.
  Rationale: Avoids runtime download instability in production job execution paths.
  Date/Author: 2026-03-26 / Codex

- Decision: Video support will be delivered in two steps: async video-job processing first, then low-latency WebSocket streaming.
  Rationale: Async video jobs reuse existing queue/polling reliability and reduce implementation risk before introducing stream-state complexity.
  Date/Author: 2026-03-26 / Codex

- Decision: `orddc2024-phase2-ensemble` is the default planned model preset for video inference, while Phase 1 remains optional for quality-focused offline runs.
  Rationale: Phase 2 provides better speed characteristics and is the practical default for user-facing video workflows.
  Date/Author: 2026-03-26 / Codex

- Decision: Add a dedicated video-job contract document now, while keeping image-job API contracts unchanged.
  Rationale: Separates upcoming video semantics from stable image MVP behavior and keeps beginner-facing docs clear.
  Date/Author: 2026-03-26 / Codex

- Decision: Default ORDDC runtime python path now targets `D:\anaconda3\envs\orddc2024\python.exe` with overridable env var (`ORDDC2024_PYTHON_PATH`).
  Rationale: User-confirmed dedicated ORDDC environment reduces dependency mismatch risk and enabled successful real-image execution.
  Date/Author: 2026-03-26 / Codex

- Decision: Inference GUI now includes an engine-family filter and grouped model selector as Milestone 3D baseline UX.
  Rationale: Multi-engine model inventory is now active and needs clearer, beginner-friendly selection controls.
  Date/Author: 2026-03-26 / Codex

- Decision: ORDDC adapter command arguments must use absolute paths and runtime error summarization must prioritize traceback tails over warning prefixes.
  Rationale: Prevents path-resolution failures in real deployments and exposes actionable root-cause errors in UI/API payloads.
  Date/Author: 2026-03-26 / Codex

- Decision: Upload validation now enforces extension-consistent image signature checks (`jpeg/png`) before job persistence.
  Rationale: Prevents non-image payloads and mismatched file content from entering engine execution paths.
  Date/Author: 2026-03-27 / Codex

- Decision: Job execution now uses atomic queued-claim and conditional success-finalization (`running` + `error_code is null`) with structured lifecycle logs.
  Rationale: Reduces duplicate execution race risk, protects cancellation semantics, and improves operability for triage.
  Date/Author: 2026-03-27 / Codex
## Outcomes & Retrospective

This section must be updated at each milestone completion. At full completion, summarize delivered user-visible behavior, unresolved gaps, and lessons for v2 multi-engine scaling.

Milestone 2A outcome (2026-03-22): backend now exposes auth-protected model listing and async inference job contract with queued persistence. Remaining work moves to Milestone 2B for real `rddc2020` command execution and status transitions beyond queued.

Milestone 2B integration outcome (2026-03-22): backend now executes `rddc2020` through per-job isolated workspace/output paths and transitions jobs `queued -> running -> succeeded/failed/cancelled` with persisted result/error metadata.

Milestone 2B hardening outcome (2026-03-22): job detail payloads now normalize to the declared detection schema, SQLite startup migration backfills Milestone 2B columns safely for older databases, adapter execution has explicit timeout classification, and startup reconciles queued/running jobs with documented durability limits.

Milestone 2C backend outcome (2026-03-22): auth-protected /history now returns user-scoped paginated job history with optional model filter and safe computed detection stats, while /inference/jobs/{job_id} remains the polling endpoint for status/detail retrieval.

Milestone 2D frontend outcome (2026-03-22): UI now supports protected inference and history navigation, image-job submission with model selection, automatic queued/running polling, terminal-state result/error rendering, and paginated history browsing with model filter and deep-link reopen to a prior job.

Workflow governance outcome (2026-03-22): Team workflow now includes a dedicated Test Engineer role with reproducible bug reporting templates, Team Leader triage/assignment templates, and mandatory retest verification before issue closure.

Bugfix closure outcome (2026-03-22): reopened UI defects `BUG-20260322-001/002` were resolved and closed after verification, with inference status updates now protected against stale polling responses and elapsed runtime display locked to `mm:ss`.

Bugfix closure outcome (2026-03-23): integration defect BUG-20260322-003 (authenticated inference image rendering path) was verified and closed after backend endpoint + frontend blob-render flow confirmation.

Bugfix stabilization outcome (2026-03-23): reopened defects BUG-20260322-001/002 were re-closed after direct patching of UTC timestamp serialization/parsing and non-overlapping polling, with user confirmation that timer and terminal auto-update behaviors are now correct.

QA workflow implementation outcome (2026-03-23): frontend automation is now active with Vitest (unit) and Playwright (smoke E2E), and was validated in this repo with passing `npm run test:unit`, `npm run test:e2e:smoke`, and `npm run build` checks.

History management outcome (2026-03-24): users can now delete one history record or clear all their own history, and /history supports explicit page-size selection (10/20/50) with safe pagination reset and refresh behavior after mutations.

Workflow ownership outcome (2026-03-25): QA process now requires Test Engineer executed-command evidence for each bug/retest cycle; Team Leader validates evidence quality and no longer performs routine closure tests.

Feature batch outcome (2026-03-25): inference UI now restores the previously selected model after manual refresh, job cards expose cancellation for queued/running states, and history UI/API support sorting by time/id/name with asc/desc ordering.

Verification outcome (2026-03-25): Test Engineer gate passed after retest (`backend pytest: 32 passed`, `frontend unit: 16 passed`, `frontend e2e smoke: 3 passed`) and issue batch was closed.

UX theme/content outcome (2026-03-25): history cards now present picture filename as primary title with model name context, and users can toggle/persist light or dark theme across login/register/dashboard/inference/history pages.

Verification outcome (2026-03-25): Test Engineer retest passed for this UX batch (`backend pytest: 32 passed`, `frontend unit: 19 passed`, `frontend e2e smoke: 3 passed`).

Documentation sync outcome (2026-03-25): repository-owned Markdown docs were audited and updated to reflect current endpoints, statuses, UX behavior, QA ownership model, and operations checks after Milestone 2 completion.

Second-engine planning outcome (2026-03-26): ORDDC2024 runtime/report/codebase were analyzed and a no-code implementation blueprint was documented, including phase-presets strategy, workspace contract mapping, and validation gates for Milestone 3C.

Video-support planning outcome (2026-03-26): ORDDC2024 video feasibility was assessed from local report evidence; team will implement async video jobs first (Phase 4A) and keep WebSocket streaming as a follow-up (Phase 4B), with ORDDC2024 Phase 2 as default video model candidate.

Milestone 3C implementation outcome (2026-03-26): backend now registers `orddc2024-cli` as second engine, exposes Phase1/Phase2 presets in `/models`, and executes ORDDC image jobs through the existing async `/inference/jobs` lifecycle with normalized outputs.

Milestone 3C verification outcome (2026-03-26): Test Engineer confirmed real-image ORDDC Phase2 inference success via API (`queued -> succeeded`), with result payload including detections and image refs.

Milestone 3D outcome (2026-03-26): inference UI now includes engine-family filtering and grouped multi-engine model options with safe persisted-selection fallback behavior; Test Engineer passed unit and smoke verification.

Bugfix outcome (2026-03-26): ORDDC runtime failure after ~30s was resolved by switching adapter command paths to absolute and improving runtime error-tail extraction; Test Engineer retest passed for both `orddc2024-phase1-ensemble` and `orddc2024-phase2-ensemble`.

Milestone 3 hardening outcome (2026-03-27): backend now rejects invalid/mismatched image bytes (`INVALID_IMAGE_CONTENT`), emits structured inference lifecycle logs (`job_id/model_id/engine_id/status/error_code/duration`), and enforces atomic queued-claim with cancellation-safe success finalization; Test Engineer verified milestone suites (`test_inference_jobs`, `test_inference_execution`, `test_history`) passing (`28 passed`).

Confidence UI outcome (2026-03-27): inference detection and history cards no longer render confidence/max-confidence in frontend; backend confidence fields remain unchanged for future engine upgrades.

## Context and Orientation

Current state includes a working Milestone 2 MVP in `backend/` and `frontend/` (auth, models, async inference jobs, authenticated job-image retrieval, and history). The first inference runtime integrated is the sibling directory `D:\road_defect_detection\rddc2020`, with its primary script at `D:\road_defect_detection\rddc2020\yolov5\detect.py`.

In this repository, an inference engine means an implementation that can execute inference jobs and return normalized outputs. An inference adapter means the backend interface layer that maps generic job requests into engine-specific execution details.

The first engine is `rddc2020-cli`. Future engines (for example, other YOLO repos or model servers) must be addable without changing frontend API contracts.

## Plan of Work

Milestone 2A defines adapter contracts and async job API shapes. Add backend service interfaces for model registry, job dispatch, and result normalization with explicit engine boundary.

Milestone 2B is complete. `rddc2020` execution now runs in per-job isolated workspace/output directories so `results.csv` and output paths do not collide across jobs. Current runtime uses in-process execution with startup reconciliation; external worker/queue is deferred to later hardening.

Milestone 2C implements persistence and retrieval. Store job status transitions (`queued`, `running`, `succeeded`, `failed`, `cancelled`) and history metadata tied to user and model. Surface results through job detail and history endpoints.

Milestone 2D is complete. Frontend now uses async job create + polling flow, renders queued/running/succeeded/failed/cancelled states, displays result metadata/detections, and provides history navigation with filters and job deep-links.

Milestone 3C is complete. The second engine (`orddc2024-cli`) is integrated through the existing adapter contract and async job APIs, with Phase 1 and Phase 2 ORDDC scripts exposed as model presets without frontend/API contract changes.

Milestone 3D is complete. Frontend inference UX now supports multi-engine model selection with engine-family filtering and grouped options.

Milestone 4A (planned) adds async video inference jobs (`create + poll + cancel`) reusing current lifecycle patterns and history model with video-specific result metadata.

Milestone 4B (planned) adds optional WebSocket streaming for near-real-time frame inference after Milestone 4A stabilizes.

## Concrete Steps

All commands below are run from repository root `D:\road_defect_detection\frondend-backend-system` unless stated otherwise.

Backend and frontend baseline (already completed):

    cd backend
    .\.venv\Scripts\python.exe -m pytest tests

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
    docs/engineering/test-engineer-workflow.md
    docs/architecture/orddc2024-integration-design.md
    docs/contracts/video-inference-job-contract.md
    docs/architecture/video-support-design.md

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
Plan change note (2026-03-22 / Codex): Implemented Milestone 2C backend history endpoint with user-scoped pagination/filtering and robust computed stats handling; added endpoint tests.
Plan change note (2026-03-22 / Codex): Independently reviewed Milestone 2C implementation after delegation (`@Ptolemy`), validated no blocking findings, and re-ran backend tests (`19 passed`).
Plan change note (2026-03-22 / Codex): Delegated Milestone 2D frontend implementation to a dedicated GPT-5.4 UI worker (`@Anscombe`), then fixed final TypeScript precedence issue and completed build-clean handoff.
Plan change note (2026-03-22 / Codex): Independently reviewed Milestone 2D frontend changes in main workflow and re-ran `frontend` build successfully.
Plan change note (2026-03-22 / Codex): Added Test Engineer workflow governance docs (role responsibilities, bug lifecycle, and standard reporting/assignment/retest templates).
Plan change note (2026-03-22 / Codex): Closed `BUG-20260322-001` and `BUG-20260322-002` via Team Leader triage -> FE delegation (`@Anscombe`) -> independent build validation -> Test Engineer retest pass (`@Confucius`).
Plan change note (2026-03-23 / Codex): Applied direct regression stabilization for `BUG-20260322-001/002` (UTC timestamp normalization + non-overlapping polling), revalidated backend tests/frontend build, and confirmed user-side closure.
Plan change note (2026-03-23 / Codex): Updated QA governance docs for planned Vitest + Playwright adoption and briefed Test Engineer workflow expectations.
Plan change note (2026-03-23 / Codex): Implemented frontend testing workflow end-to-end (Vitest/Playwright config + tests + scripts), validated runtime compatibility, and updated documentation + usage guidance.
Plan change note (2026-03-24 / Codex): Implemented history feature batch (delete-one, clear-all, page-size selector), integrated backend/frontend tests, and updated API/UI contracts + ExecPlan tracking.
Plan change note (2026-03-25 / Codex): Updated workflow governance so Test Engineer executes Vitest/Playwright/pytest evidence runs and Team Leader performs supervision-only closure gating.
Plan change note (2026-03-25 / Codex): Implemented user-requested feature batch (model persistence, job cancellation, history sorting), triaged post-implementation test blockers to FE/BE owners, and closed with Test Engineer retest evidence.
Plan change note (2026-03-25 / Codex): Implemented history card content update (picture title + model name) and persistent light/dark theme toggle, then closed with Test Engineer verification evidence.
Plan change note (2026-03-25 / Codex): Audited all project-owned Markdown files and synchronized docs to current Milestone 2 API/UX/workflow/operations state.

Plan change note (2026-03-26 / Codex): Added ORDDC2024 second-engine integration planning docs and updated ExecPlan decisions/discoveries for Milestone 3C execution readiness.
Plan change note (2026-03-26 / Codex): Added video-support feasibility decisions and synced architecture/contracts/UX docs for planned Milestone 4A (async video jobs) and 4B (WebSocket streaming).
Plan change note (2026-03-26 / Codex): Implemented Milestone 3C backend integration (`orddc2024` adapter + config + registry + tests) and validated real-image ORDDC runtime success through Test Engineer evidence.
Plan change note (2026-03-26 / Codex): Implemented Milestone 3D frontend multi-engine UX (engine-family selector + grouped models) and closed with Test Engineer unit/smoke verification.
Plan change note (2026-03-26 / Codex): Closed ORDDC post-release runtime failure by fixing absolute path command args and traceback-tail error reporting; verified Phase1/Phase2 success with Test Engineer evidence.
Plan change note (2026-03-27 / Codex): Implemented Milestone 3 hardening (upload content validation, structured job logging, atomic job claim/finalization safety) and aligned backend integration tests with Test Engineer verification evidence.
Plan change note (2026-03-27 / Codex): Applied UI-only confidence policy (removed confidence/max-confidence display in frontend, retained backend confidence contract) and synchronized docs.

