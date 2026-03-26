# Video Inference Job Contract (Planned)

Status: planning approved, implementation not started.

Date: 2026-03-26.

## Purpose

Define a beginner-friendly, API-first contract for video inference that extends the existing async image-job pattern without breaking current MVP endpoints.

## Phase Strategy

- Phase 4A (planned first): asynchronous video jobs (`create -> poll -> cancel`).
- Phase 4B (planned next): optional WebSocket streaming for near-real-time frame results.

This document defines Phase 4A. WebSocket details are captured in `docs/contracts/realtime-websocket-contract.md`.

## Planned Endpoints (Phase 4A)

- `POST /inference/video/jobs`
- `GET /inference/video/jobs/{job_id}`
- `POST /inference/video/jobs/{job_id}/cancel`

History remains under existing `GET /history` with planned job-type metadata so image and video jobs can coexist in one timeline.

## Create Video Job Request

Multipart form data:

- `video_file` (required): allowed extensions: `.mp4`, `.mov`, `.avi`, `.mkv`.
- `model_id` (required): must be active and video-capable in model registry.
- `sample_fps` (optional): frame sampling rate for inference (default planned: `2` on CPU baseline).

## Create Video Job Response

```json
{
  "job_id": "uuid",
  "status": "queued",
  "job_type": "video",
  "model_id": "orddc2024-phase2-ensemble",
  "engine_id": "orddc2024-cli",
  "created_at": "2026-03-26T10:00:00Z"
}
```

## Video Job Lifecycle

Planned statuses:

- `queued`
- `preparing_frames`
- `running`
- `rendering`
- `succeeded`
- `failed`
- `cancelled`

Terminal statuses: `succeeded`, `failed`, `cancelled`.

## Job Detail Success Shape

```json
{
  "job_id": "uuid",
  "job_type": "video",
  "status": "succeeded",
  "model_id": "orddc2024-phase2-ensemble",
  "engine_id": "orddc2024-cli",
  "started_at": "2026-03-26T10:00:03Z",
  "finished_at": "2026-03-26T10:01:28Z",
  "result": {
    "video_refs": {
      "input_video": "/internal/path/or/url",
      "annotated_video": "/internal/path/or/url"
    },
    "summary": {
      "frames_processed": 120,
      "sample_fps": 2,
      "total_detections": 86,
      "labels": {
        "crack": 45,
        "pothole": 41
      }
    },
    "frame_results": [
      {
        "frame_id": "f-0001",
        "timestamp_ms": 500,
        "detections": [
          {
            "label": "crack",
            "confidence": 0.91,
            "bbox": {"x1": 10, "y1": 21, "x2": 89, "y2": 67}
          }
        ],
        "image_refs": {
          "annotated": "/internal/path/or/url"
        }
      }
    ]
  }
}
```

## Error Behavior

- Same standard API error envelope (`code`, `message`, `request_id`).
- Planned video-specific codes:
  - `INVALID_VIDEO_FILE`
  - `VIDEO_TOO_LARGE`
  - `VIDEO_TOO_LONG`
  - `VIDEO_DECODE_FAILED`
  - `MODEL_NOT_VIDEO_CAPABLE`
  - `VIDEO_RENDER_FAILED`

## Registry Compatibility Rule

A model preset used for `POST /inference/video/jobs` must expose planned capability metadata:

- `supports_image`: `true|false`
- `supports_video`: `true|false`
- `supports_streaming`: `true|false`

Planned default for first video rollout: `orddc2024-phase2-ensemble`.

## Acceptance Targets (Planning)

- User can submit, poll, and cancel a video job without affecting image-job endpoints.
- Video result returns both summary stats and frame-level detections.
- History can list both image and video jobs with clear type labels.
- Unsupported model and invalid video input fail with explicit validated errors.
