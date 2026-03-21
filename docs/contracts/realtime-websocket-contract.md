# Phase 2 WebSocket Contract

This contract is reserved for real-time streaming implementation after image MVP stability.

## Endpoint

- `GET /ws/inference` (WebSocket upgrade)

## Session Rules

- Client must provide valid auth token at connection.
- Client must provide selected `model_name` when session starts.
- Model remains fixed during session.
- To change model, client must close stream and reconnect with new model.

## Message Shapes

Client -> Server (frame payload):

```json
{
  "type": "frame",
  "frame_id": "f-001",
  "timestamp": "2026-03-21T11:00:00Z",
  "image_base64": "..."
}
```

Server -> Client (annotated result):

```json
{
  "type": "result",
  "frame_id": "f-001",
  "model_name": "yolov8n",
  "detections": [
    {"label": "crack", "confidence": 0.91, "bbox": {"x1": 11, "y1": 20, "x2": 88, "y2": 64}}
  ],
  "annotated_image_base64": "...",
  "latency_ms": 124
}
```

Server -> Client (error):

```json
{
  "type": "error",
  "code": "INVALID_MODEL",
  "message": "Model is not active.",
  "request_id": "uuid"
}
```

## Persistence

Phase 2 should persist stream session summaries in history while keeping per-frame storage optional.