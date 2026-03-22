# API to UI Mapping Matrix

This matrix ties each UI screen to backend endpoints and expected response states.

| Screen | Endpoint(s) | Loading State | Success State | Error State | Empty State |
|---|---|---|---|---|---|
| Login | `POST /auth/login` | Disable form and show spinner | Persist token and redirect dashboard | Show credential error message | N/A |
| Register | `POST /auth/register` | Disable form and show spinner | Route to dashboard after auth payload | Show validation field errors | N/A |
| Dashboard | `GET /models` | Skeleton cards | Actions enabled | Non-blocking alert | If models unavailable, fallback message |
| Image Inference Submit | `GET /models`, `POST /inference/jobs` | Disable submit and show queue state | Show `job_id` and start polling | Show API error with retry | Before first run show upload prompt |
| Image Inference Poll | `GET /inference/jobs/{job_id}` (polling) | Show `queued/running` status indicator | Render annotated image + detections on `succeeded` | Show failure state on `failed` | N/A |
| History | `GET /history` | Table skeleton | Render job list with statuses and details | Show retry alert | Show no-history illustration |

## UI State Contract Rules

- All network failures must map to standard API error envelope fields (`code`, `message`, `request_id`).
- Unauthorized responses (`401`) must clear auth state and redirect to login.
- Job polling must stop when terminal status (`succeeded` or `failed`) is reached.
- Queued/running states must be visible to user with clear progress messaging.
- Failed jobs must show error summary and retry action.