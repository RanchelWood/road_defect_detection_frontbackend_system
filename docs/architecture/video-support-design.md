# Video Support Design (Planning Only)

Status: planning approved, implementation not started.

Date: 2026-03-26.

## Goal

Add video inference capability without destabilizing existing MVP image flows. The rollout should prefer reliability first, then low-latency streaming.

## Inputs Consulted

- `D:\road_defect_detection\orddc2024-main\VIDEO_INFERENCE_SUPPORT_REPORT.md`
- `D:\road_defect_detection\orddc2024-main\INFERENCE_INTEGRATION_REPORT.md`
- Local backend adapter architecture and contracts in this repository.

## Feasibility Verdict

Feasible with staged implementation. ORDDC2024 can be reused for video by converting video into frame batches and aggregating results, but its current scripts are image-oriented and require orchestration around decoding, batching, and rendering.

## Rollout Strategy

- Milestone 4A: Async video jobs (`POST/GET/cancel`) with queue + polling model.
- Milestone 4B: WebSocket streaming (`/ws/inference`) after async path is stable.

## Recommended Engine/Model Defaults

- Default video model: `orddc2024-phase2-ensemble` (speed-oriented).
- Optional quality-heavy mode: `orddc2024-phase1-ensemble` for offline use where latency is less critical.

## Planned 4A Pipeline (Async Video Jobs)

1. Upload video and validate format/size/duration.
2. Create job (`queued`) and allocate per-job workspace.
3. Decode/extract sampled frames (`preparing_frames`).
4. Run inference on sampled frames via adapter (`running`).
5. Aggregate detections and render optional annotated output video (`rendering`).
6. Persist summary + frame results and finish (`succeeded`/`failed`/`cancelled`).

## Workspace and Output Contract (Planned)

Per video job workspace:

- `input_video/`
- `frames_raw/`
- `frames_annotated/`
- `results_frames.csv` (or normalized json)
- `output_video/annotated.mp4`
- `run_log.md`

## Planned Data/Contract Additions

- Job type discriminator: `image | video`.
- Video-specific lifecycle statuses (`preparing_frames`, `rendering`).
- Result summary fields: processed frames, sampled fps, per-label counts, output references.
- Model capability metadata: `supports_image`, `supports_video`, `supports_streaming`.

Detailed API shape: `docs/contracts/video-inference-job-contract.md`.

## Operational Constraints (CPU-First)

Suggested first limits for stable rollout:

- Max upload size and max duration limits enabled.
- Frame sampling rate default (for example 2 fps on CPU).
- Hard timeout and cancellation support for long jobs.
- Backpressure rule: limited concurrent video jobs.

## Risks and Mitigations

- CPU latency spikes on long/high-resolution video.
  - Mitigation: strict upload limits, frame sampling, queue concurrency caps.
- Decode/render toolchain failures.
  - Mitigation: explicit preflight checks and dedicated error codes.
- Large artifact storage growth.
  - Mitigation: retention policy for intermediate frames and optional annotated video generation.
- Contract drift between image and video job payloads.
  - Mitigation: shared envelope + explicit `job_type` and versioned docs.

## Acceptance Criteria (Planning)

- Async video jobs run end-to-end with predictable status transitions.
- Users can cancel queued/running video jobs safely.
- History clearly distinguishes image vs video jobs.
- Existing image inference flows remain unchanged.

## Out of Scope for 4A

- Live webcam streaming.
- Mid-session model hot swap.
- Multi-node distributed video workers.

These are candidates after 4A stabilization and 4B streaming readiness.
