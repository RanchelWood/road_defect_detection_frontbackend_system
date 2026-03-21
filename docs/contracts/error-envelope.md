# Standard Error Envelope

All backend errors must use this JSON envelope so frontend handling remains uniform.

## Envelope

```json
{
  "success": false,
  "error": {
    "code": "INVALID_MODEL",
    "message": "Model 'abc' is not supported.",
    "details": {
      "field": "model_name"
    }
  },
  "meta": {
    "request_id": "9b529953-0c8c-4a8d-bf59-4f1d03a27f8f",
    "timestamp": "2026-03-21T10:30:00Z"
  }
}
```

## Required Fields

- `success`: always `false` on error.
- `error.code`: stable machine-readable code.
- `error.message`: human-readable message for UI.
- `meta.request_id`: request trace id for logs/support.
- `meta.timestamp`: UTC ISO timestamp.

## Common Error Codes

- `AUTH_INVALID_CREDENTIALS`
- `AUTH_TOKEN_EXPIRED`
- `AUTH_TOKEN_INVALID`
- `AUTH_FORBIDDEN`
- `VALIDATION_ERROR`
- `INVALID_FILE_TYPE`
- `FILE_TOO_LARGE`
- `INVALID_MODEL`
- `INFERENCE_FAILED`
- `NOT_FOUND`
- `INTERNAL_ERROR`