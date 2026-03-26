# Standard Error Envelope

All backend HTTP errors use this JSON envelope so frontend handling remains uniform.

## Envelope

```json
{
  "success": false,
  "error": {
    "code": "INVALID_MODEL",
    "message": "Model 'x' is not supported.",
    "details": {
      "field": "model_id"
    }
  },
  "meta": {
    "request_id": "9b529953-0c8c-4a8d-bf59-4f1d03a27f8f",
    "timestamp": "2026-03-22T10:30:00Z"
  }
}
```

## Required Fields

- `success`: always `false` on HTTP error responses.
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

Inference/job and media access:

- `NOT_FOUND`
- `INVALID_IMAGE_KIND`
- `IMAGE_NOT_FOUND`

Engine/runtime-related codes surfaced in job detail payloads (`GET /inference/jobs/{job_id}` `data.error`):

- `ENGINE_NOT_RUNNABLE`
- `ENGINE_NOT_AVAILABLE`
- `ENGINE_RUNTIME_ERROR`
- `ENGINE_OUTPUT_MISSING`
- `ENGINE_OUTPUT_PARSE_ERROR`
- `ENGINE_TIMEOUT`
- `JOB_CANCELLED`

## Notes

- Cancellation is represented as terminal job status `cancelled` and is not returned as an HTTP error by the cancel endpoint.
- Frontend should treat `401` as a session reset event and redirect to login.
