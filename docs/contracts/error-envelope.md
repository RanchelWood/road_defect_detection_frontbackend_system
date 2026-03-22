# Standard Error Envelope

All backend errors must use this JSON envelope so frontend handling remains uniform.

## Envelope

```json
{
  "success": false,
  "error": {
    "code": "ENGINE_EXECUTION_FAILED",
    "message": "Inference engine command failed.",
    "details": {
      "job_id": "a2b6..."
    }
  },
  "meta": {
    "request_id": "9b529953-0c8c-4a8d-bf59-4f1d03a27f8f",
    "timestamp": "2026-03-22T10:30:00Z"
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

Auth and validation:

- `AUTH_INVALID_CREDENTIALS`
- `AUTH_TOKEN_EXPIRED`
- `AUTH_TOKEN_INVALID`
- `AUTH_FORBIDDEN`
- `VALIDATION_ERROR`
- `INVALID_FILE_TYPE`
- `FILE_TOO_LARGE`
- `INVALID_MODEL`

Job and engine integration:

- `JOB_NOT_FOUND`
- `JOB_NOT_READY`
- `JOB_ALREADY_FINISHED`
- `ENGINE_UNAVAILABLE`
- `ENGINE_EXECUTION_FAILED`
- `ENGINE_OUTPUT_PARSE_FAILED`
- `ENGINE_TIMEOUT`

Generic:

- `NOT_FOUND`
- `INTERNAL_ERROR`