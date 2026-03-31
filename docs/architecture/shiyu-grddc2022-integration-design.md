# ShiYu GRDDC2022 Third-Engine Integration Design

Status: Milestone 3E implemented (core integration + dynamic frontend family filtering). Milestone 3F core implementation landed and is awaiting final runtime smoke closure evidence.  
Phase follow-up: close Milestone 3F with runtime verification for the demo two-stage preset.

Date: 2026-03-31.

## Goal

Integrate `ShiYu_SeaView_GRDDC2022` as a third image-inference engine through the existing adapter contract and async job APIs, without changing public endpoint shapes.

## Inputs Consulted

- `D:\road_defect_detection\ShiYu_SeaView_GRDDC2022\INTEGRATION_REPORT_SHIYU_TO_FRONTEND_BACKEND_SYSTEM_2026-03-24.md`
- `D:\road_defect_detection\ShiYu_SeaView_GRDDC2022\yolov7\detect.py`
- `D:\road_defect_detection\ShiYu_SeaView_GRDDC2022\yolov5\detect.py`
- `D:\road_defect_detection\ShiYu_SeaView_GRDDC2022\merge.py`

## Feasibility Verdict

Feasible with moderate adapter orchestration complexity.

- Parser complexity: low (line format is `filename,class x1 y1 x2 y2 ...`).
- Orchestration complexity: moderate (multi-step ensemble flow + merge + final overlay render).
- API impact: none (existing `/models`, `/inference/jobs`, polling, and image endpoint contracts are retained).

## Implemented Milestone 3E Scope

### Engine and presets

Engine ID:

- `shiyu-grddc2022-cli`

Implemented presets:

- `shiyu-cpu-ensemble-default`
  - YOLOv7 detect
  - YOLOv5 detect
  - `merge.py`
  - parse merged output
- `shiyu-yolov7x-640`
  - YOLOv7 detect
  - parse direct output
- `shiyu-y7x640-faster-swin-w7`
  - YOLOv7 detect
  - MMDetection Faster-Swin-L W7 step
  - `merge.py`
  - parse merged output

### Runtime wiring

Added runtime settings:

- `shiyu_grddc2022_python_path`
- `shiyu_grddc2022_root`
- `shiyu_grddc2022_device`
- `shiyu_grddc2022_timeout_seconds_single`
- `shiyu_grddc2022_timeout_seconds_ensemble`
- `shiyu_grddc2022_timeout_seconds_mmdet`
- `shiyu_grddc2022_mmdet_config`
- `shiyu_grddc2022_mmdet_checkpoint`

Defaults are CPU-first and aligned to local machine paths.

### Execution contract mapping

For each job:

1. Create isolated workspace with per-step logs/output files.
2. Copy uploaded image into job-local source directory.
3. Execute preset-owned steps with absolute command paths.
4. Parse detection output to normalized payload (`label`, `confidence: null`, `bbox`).
5. Save final annotated image path for existing authenticated image endpoint.

### Deterministic failure semantics

Adapter returns explicit errors for:

- missing runtime/scripts/weights
- timeout
- non-zero subprocess exit
- missing or empty output files
- parse failures

Messages include failed step context for multi-step ensemble troubleshooting.

### Ensemble annotated image policy

For ensemble jobs, final annotated image is rendered from merged detections over original upload.
Child model overlays are not used as final artifact.

Post-release runtime hardening (2026-03-28):

- If `Pillow` is unavailable in backend runtime, adapter does not fail the job.
- Fallback behavior copies original image to annotated output path so result endpoints remain usable.
- Detection payload remains unchanged; this fallback only affects visual overlay rendering.

## Frontend impact in Milestone 3E

No API contract changes.

Inference page engine-family selector now derives family options dynamically from `/models`, with known-label mapping for:

- `rddc2020-cli -> RDDC2020`
- `orddc2024-cli -> ORDDC2024`
- `shiyu-grddc2022-cli -> GRDDC2022`

Unknown engines use normalized engine-id fallback labels.

## Milestone 3F Scope (Implementation Landed)

Implemented additional GRDDC2022 demonstration preset:

- `shiyu-y7x640-faster-swin-w7`
  - YOLOv7 detect
  - MMDetection Faster-Swin-L W7 inference step
  - merge

Milestone 3F closure is gated on Test Engineer runtime smoke evidence for this preset in the integrated web flow.

## Acceptance Criteria

- `/models` exposes all active `shiyu-*` presets under `shiyu-grddc2022-cli`, including `shiyu-y7x640-faster-swin-w7`.
- `POST /inference/jobs` with `shiyu-cpu-ensemble-default`, `shiyu-yolov7x-640`, and `shiyu-y7x640-faster-swin-w7` returns queued job and reaches terminal status.
- Successful jobs return normalized detections and authenticated annotated image.
- Ensemble annotated image reflects merged detections.
- If backend runtime lacks `Pillow`, annotated endpoint still serves fallback copied image rather than failing job.
- Existing engines (`rddc2020`, `orddc2024`) remain unaffected.

