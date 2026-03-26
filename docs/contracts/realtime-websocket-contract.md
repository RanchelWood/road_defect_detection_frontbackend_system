# Phase 4B WebSocket Contract (Planned)

Status: planning only. Not implemented yet.

This contract is reserved for real-time streaming implementation after image-job MVP stability and async video-job rollout.

## Endpoint

- `GET /ws/inference` (WebSocket upgrade)

## Relationship to Async Video Jobs

- Phase 4A async video jobs are the first delivery target.
- WebSocket streaming is Phase 4B and should not replace polling endpoints.
- Polling (`/inference/jobs` and planned `/inference/video/jobs`) remains compatibility baseline.

## Session Rules

- Client must provide valid auth token at connection.
- Client must provide selected `model_id` when session starts.
- Backend resolves `model_id` to engine/model preset and validates `supports_streaming=true`.
- Model remains fixed during session.
- To change model, client must close stream and reconnect with new `model_id`.
- Planned first streaming candidate: `orddc2024-phase2-ensemble`.

## Message Shapes

Client -> Server (frame payload):

```json
{
  "type": "frame",
  "frame_id": "f-001",
  "timestamp": "2026-03-26T10:00:00Z",
  "image_base64": "..."
}
```

Server -> Client (annotated result):

```json
{
  "type": "result",
  "frame_id": "f-001",
  "model_id": "orddc2024-phase2-ensemble",
  "engine_id": "orddc2024-cli",
  "detections": [
    {"label": "crack", "confidence": 0.91, "bbox": {"x1": 11, "y1": 20, "x2": 88, "y2": 64}}
  ],
  "annotated_image_base64": "...",
  "latency_ms": 124
}
```

Server -> Client (status):

```json
{
  "type": "status",
  "state": "running",
  "session_id": "ws-uuid",
  "model_id": "orddc2024-phase2-ensemble"
}
```

Server -> Client (error):

```json
{
  "type": "error",
  "code": "INVALID_MODEL",
  "message": "Model is not active or not stream-capable.",
  "request_id": "uuid"
}
```

## Persistence

Phase 4B should persist stream session summaries in history while keeping per-frame storage optional.

## Planning References

- `docs/contracts/video-inference-job-contract.md`
- `docs/architecture/video-support-design.md`
