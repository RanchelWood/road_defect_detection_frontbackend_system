# ORDDC2024 Second-Engine Integration Design (Planning Only)

Status: planning approved, code implementation not started.

Date: 2026-03-26.

## Goal

Integrate `orddc2024` as the second inference engine without breaking the existing image-job API, frontend flow, or first-engine (`rddc2020`) behavior.

## Inputs Consulted

- `D:\road_defect_detection\orddc2024-main\INFERENCE_INTEGRATION_REPORT.md`
- `D:\road_defect_detection\orddc2024-main\inference_script_v2_Phase1.py`
- `D:\road_defect_detection\orddc2024-main\inference_script_v2_Phase2.py`
- `D:\road_defect_detection\orddc2024-main\model_ph1.yaml`
- `D:\road_defect_detection\orddc2024-main\model_ph2.yaml`
- local project adapter contracts/docs in this repository

## Feasibility Verdict

Feasible with moderate adapter work. The current backend adapter contract can support ORDDC2024, but ORDDC2024 runtime expects a directory-based input/output contract and phase-specific scripts. This requires translation logic in a new adapter, not API changes.

## Key Runtime Facts (From ORDDC2024)

- Entry points:
  - `inference_script_v2_Phase1.py`
  - `inference_script_v2_Phase2.py`
- Required CLI shape:
  - `python <phase_script> <images_dir> <output_csv> [boxed_output_dir]`
- Script behavior:
  - Writes a submission-style CSV (`filename,class x1 y1 x2 y2 ...`)
  - Writes boxed image files when boxed output path is passed
  - Uses model directories `models_ph1` / `models_ph2`
  - Auto-downloads models with `gdown` when cache is missing
- Observed warning behavior:
  - `pkg_resources` warning appears on stderr even on successful runs

## Contract Mapping to Current Backend

Current backend adapter contract receives one uploaded image path and one job workspace path. ORDDC2024 expects image directory input.

Planned mapping:

1. Create per-job workspace:
   - `<job_workspace>/image_root/`
   - `<job_workspace>/results.csv`
   - `<job_workspace>/boxed_output/`
   - `<job_workspace>/run_log.md`
2. Copy single uploaded image into `image_root`.
3. Run phase script in ORDDC2024 root directory.
4. Parse `results.csv` for the uploaded filename.
5. Use boxed image at `boxed_output/<filename>` as annotated result.
6. Normalize detections into existing API format (`label`, `confidence`, `bbox`).

## Model/Phase Strategy

Keep frontend and API unchanged by exposing phase selection as model presets.

Planned presets:

- `orddc2024-phase1-ensemble`
- `orddc2024-phase2-ensemble`

Both use `engine_id = orddc2024-cli` and `runtime_type = cli`.

## Runtime Invocation Strategy

Decision:

- Use direct `python` executable invocation from backend adapter (same style as current `rddc2020` adapter).
- Do not require Git Bash in backend process execution path.

Rationale:

- More stable process management for timeout/cancel handling.
- Avoid shell quoting/path edge cases.
- Matches current adapter architecture.

## Preflight and Failure Policy

Success only when all conditions pass:

- process exit code is `0`
- `results.csv` exists and has at least one line
- boxed image for target filename exists

Fail with explicit adapter error codes otherwise.

Recommended operational default:

- pre-provision `models_ph1` and `models_ph2`
- do not rely on runtime auto-download in production

(An optional future env flag may allow auto-download for developer environments.)

## Cancellation and Timeout

- Reuse current cooperative cancellation pattern in adapters.
- If user cancels while script runs, terminate process and report `JOB_CANCELLED`.
- Use dedicated ORDDC timeout config (expected to be longer than rddc2020 phase runs).

## Risks and Mitigations

- Long CPU runtime in Phase 1 (many ensemble weights):
  - Mitigation: phase-specific performance notes, timeout sizing, clear UI messaging.
- Auto-download dependency (`gdown`) if model cache missing:
  - Mitigation: startup/runbook preflight checks and fail-fast policy.
- Warning noise on stderr:
  - Mitigation: do not treat warning text alone as failure.
- CSV format differences across future upstream updates:
  - Mitigation: strict parser + defensive validation tests.

## Implementation Breakdown (Next Coding Stage)

Milestone 3C.1: adapter scaffolding and config

- Add `orddc2024` runtime config fields (`python_path`, `root`, timeout, optional download policy).
- Add `Orddc2024Adapter` class under adapter module.

Milestone 3C.2: runtime execution and normalization

- Implement per-job workspace mapping and script invocation.
- Parse CSV and resolve boxed image output.
- Map detections into existing API schema.

Milestone 3C.3: registry exposure

- Register `orddc2024-cli` in engine registry.
- Expose phase presets in `/models` response.

Milestone 3C.4: validation and hardening

- Add unit/integration tests for parser, success/failure criteria, and cancellation.
- Add runbook checks and troubleshooting notes.
- Validate first-engine regression safety.

## Acceptance Criteria for Second-Engine Integration

- `/models` includes ORDDC2024 phase presets.
- User can submit image inference jobs using either engine family.
- Job lifecycle remains `queued -> running -> succeeded/failed/cancelled`.
- ORDDC2024 result returns annotated image and normalized detections through existing endpoints.
- Existing `rddc2020` behavior remains unchanged.

## Video Extension Note (Planning)

ORDDC2024 Phase 2 ensemble is planned as the default candidate for this project's first video rollout due to better speed characteristics on CPU compared with Phase 1. Video support itself is tracked separately so image integration can land first without blocking.

See:

- `docs/architecture/video-support-design.md`
- `docs/contracts/video-inference-job-contract.md`
